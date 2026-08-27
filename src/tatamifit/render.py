"""Deterministic TatamiFit output renderers."""

from __future__ import annotations

import json
import shutil
import tempfile
from html import escape
from pathlib import Path

from tatamifit import __version__
from tatamifit.model import Cell, Placement, Room
from tatamifit.solver import Solution


class OutputExistsError(FileExistsError):
    """Raised when a requested output path already belongs to the user."""


def write_solution(room: Room, solution: Solution, output: Path) -> None:
    """Atomically write all public artifacts to a new directory."""

    if output.exists():
        raise OutputExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        _write_text(temporary / "layout.json", render_json(room, solution))
        _write_text(temporary / "layout.svg", render_svg(room, solution))
        _write_text(temporary / "layout.txt", render_text(room, solution))
        temporary.replace(output)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def render_json(room: Room, solution: Solution) -> str:
    return json.dumps(layout_payload(room, solution), ensure_ascii=False, indent=2) + "\n"


def layout_payload(room: Room, solution: Solution) -> dict[str, object]:
    fixed = set(room.fixed)
    retained = set(solution.retained_preferred)
    placements = [
        {
            "id": identifier,
            "x": placement.x,
            "y": placement.y,
            "orientation": placement.orientation,
            "cells": [{"x": x, "y": y} for x, y in placement.cells],
            "fixed": placement in fixed,
            "retained_preferred": placement in retained,
        }
        for identifier, placement in _identified(solution.placements)
    ]
    return {
        "schema_version": 1,
        "generator": {"name": "TatamiFit", "version": __version__},
        "status": "layout_found",
        "room": {
            "name": room.name,
            "width": room.width,
            "height": room.height,
            "blocked": [
                {"x": x, "y": y}
                for x, y in sorted(room.blocked, key=lambda cell: (cell[1], cell[0]))
            ],
        },
        "summary": {
            "mat_count": len(solution.placements),
            "fixed_count": len(room.fixed),
            "preferred_count": len(room.preferred),
            "retained_count": solution.retained_count,
            "changed_count": solution.changed_count,
            "search_nodes": solution.search_nodes,
        },
        "rules": {"no_four_corners": True, "violations": []},
        "placements": placements,
    }


def render_svg(room: Room, solution: Solution) -> str:
    cell_size = 72
    top = 104
    side = 32
    bottom = 70
    grid_width = room.width * cell_size
    canvas_width = max(440, grid_width + side * 2)
    grid_left = (canvas_width - grid_width) // 2
    canvas_height = top + room.height * cell_size + bottom
    retained = set(solution.retained_preferred)
    fixed = set(room.fixed)
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_width} '
            f'{canvas_height}" role="img" aria-labelledby="title description">'
        ),
        f'  <title id="title">TatamiFit layout: {escape(room.name)}</title>',
        (
            '  <desc id="description">A complete 1-by-2 mat layout where no point '
            "lets four different mats meet.</desc>"
        ),
        '  <rect width="100%" height="100%" fill="#f7f2e8"/>',
        (
            f'  <text x="{canvas_width // 2}" y="38" text-anchor="middle" '
            f'font-family="system-ui,sans-serif" font-size="24" font-weight="700" '
            f'fill="#2c2924">{escape(room.name)}</text>'
        ),
        (
            f'  <text x="{canvas_width // 2}" y="67" text-anchor="middle" '
            f'font-family="system-ui,sans-serif" font-size="14" fill="#625b50">'
            f"{len(solution.placements)} mats · retained {solution.retained_count}/"
            f"{len(room.preferred)} preferred · 0 four-corner junctions</text>"
        ),
    ]
    for y in range(room.height):
        for x in range(room.width):
            parts.append(
                f'  <rect x="{grid_left + x * cell_size}" y="{top + y * cell_size}" '
                f'width="{cell_size}" height="{cell_size}" fill="none" stroke="#d8d0c2"/>'
            )
    for x, y in sorted(room.blocked, key=lambda cell: (cell[1], cell[0])):
        parts.append(
            f'  <rect x="{grid_left + x * cell_size + 5}" y="{top + y * cell_size + 5}" '
            f'width="{cell_size - 10}" height="{cell_size - 10}" rx="6" fill="#514c45"/>'
        )
    for identifier, placement in _identified(solution.placements):
        width = cell_size * (2 if placement.orientation == "horizontal" else 1)
        height = cell_size * (2 if placement.orientation == "vertical" else 1)
        x = grid_left + placement.x * cell_size + 5
        y = top + placement.y * cell_size + 5
        fill = "#d9b66f" if placement.orientation == "horizontal" else "#9abf9a"
        stroke = "#6e4b8f" if placement in fixed else "#3f5142"
        stroke_width = 4 if placement in retained else 2
        parts.extend(
            [
                (
                    f'  <rect x="{x}" y="{y}" width="{width - 10}" height="{height - 10}" '
                    f'rx="9" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
                ),
                (
                    f'  <text x="{x + (width - 10) // 2}" y="{y + (height - 10) // 2 + 5}" '
                    f'text-anchor="middle" font-family="ui-monospace,monospace" font-size="15" '
                    f'font-weight="700" fill="#2c2924">{identifier}</text>'
                ),
            ]
        )
    legend_y = top + room.height * cell_size + 38
    parts.append(
        f'  <text x="{canvas_width // 2}" y="{legend_y}" text-anchor="middle" '
        'font-family="system-ui,sans-serif" font-size="13" fill="#625b50">'
        "Thick border = retained preference · Purple border = fixed mat</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def render_text(room: Room, solution: Solution) -> str:
    identifiers = _identified(solution.placements)
    owner: dict[Cell, str] = {
        cell: identifier for identifier, placement in identifiers for cell in placement.cells
    }
    fixed = set(room.fixed)
    retained = set(solution.retained_preferred)
    lines = [
        f"TatamiFit layout: {room.name}",
        (
            f"Grid: {room.width}x{room.height} | Mats: {len(solution.placements)} | "
            f"Retained: {solution.retained_count}/{len(room.preferred)} | "
            f"Changed: {solution.changed_count}"
        ),
        "Rule: PASS — no four different mats meet at one point.",
        "",
    ]
    for y in range(room.height):
        lines.append(
            " ".join("###" if (x, y) in room.blocked else owner[(x, y)] for x in range(room.width))
        )
    lines.extend(("", "Placements:"))
    for identifier, placement in identifiers:
        flags = []
        if placement in fixed:
            flags.append("fixed")
        if placement in retained:
            flags.append("retained")
        suffix = f" [{' '.join(flags)}]" if flags else ""
        lines.append(
            f"- {identifier}: {placement.orientation} at ({placement.x},{placement.y}){suffix}"
        )
    return "\n".join(lines) + "\n"


def _identified(placements: tuple[Placement, ...]) -> list[tuple[str, Placement]]:
    return [(f"M{index:02d}", placement) for index, placement in enumerate(placements, start=1)]


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")
