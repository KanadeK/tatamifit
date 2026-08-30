"""TatamiFit command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from tatamifit import __version__
from tatamifit.model import InputError, Room, parse_room
from tatamifit.render import OutputExistsError, write_solution
from tatamifit.solver import solve

DEMO_ROOM: dict[str, object] = {
    "schema_version": 1,
    "name": "TatamiFit repair demo",
    "width": 4,
    "height": 4,
    "blocked": [],
    "fixed": [],
    "preferred": [{"x": x, "y": y, "orientation": "horizontal"} for y in range(4) for x in (0, 2)],
}


@dataclass(frozen=True)
class CommandError(Exception):
    code: str
    message: str
    repair: str

    def __str__(self) -> str:
        return self.message


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    if arguments.command == "plan":
        try:
            room = _load_room(arguments.input)
        except (CommandError, InputError) as error:
            _print_error(error)
            return 2
        return _plan(room, arguments.out)
    if arguments.command == "demo":
        return _plan(parse_room(DEMO_ROOM), arguments.out)
    raise AssertionError(f"unhandled command: {arguments.command}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tatamifit",
        description="Plan and repair no-four-corners 1-by-2 mat layouts.",
    )
    parser.add_argument("--version", action="version", version=f"tatamifit {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan", help="plan a room from a strict JSON input")
    plan.add_argument("input", type=Path, help="path to a v1 room JSON file")
    plan.add_argument("--out", type=Path, required=True, help="new output directory")
    demo = commands.add_parser("demo", help="run the bundled repair example")
    demo.add_argument("--out", type=Path, required=True, help="new output directory")
    return parser


def _load_room(path: Path) -> Room:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise CommandError(
            "INPUT_NOT_FOUND",
            f"Input file does not exist: {path}",
            "Check the input path and run the same command again.",
        ) from error
    except UnicodeDecodeError as error:
        raise CommandError(
            "INVALID_UTF8",
            f"Input file is not valid UTF-8: {path}",
            "Save the JSON file as UTF-8 and run the same command again.",
        ) from error
    except OSError as error:
        raise CommandError(
            "INPUT_IO_ERROR",
            f"Could not read {path}: {error}",
            "Check the file permissions and path, then run the same command again.",
        ) from error

    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        decoded_object: dict[str, object] = {}
        for field, value in pairs:
            if field in decoded_object:
                raise CommandError(
                    "DUPLICATE_FIELD",
                    f"Duplicate JSON field {field!r}.",
                    f"Remove one duplicate field named {field!r} so each object field is unique.",
                )
            decoded_object[field] = value
        return decoded_object

    try:
        decoded = json.loads(text, object_pairs_hook=unique_object)
    except json.JSONDecodeError as error:
        raise CommandError(
            "INVALID_JSON",
            f"Invalid JSON at line {error.lineno}, column {error.colno}: {error.msg}",
            "Correct the JSON syntax at that location and run the same command again.",
        ) from error
    return parse_room(decoded)


def _plan(room: Room, output: Path) -> int:
    solution = solve(room)
    if solution is None:
        print(
            (
                f"NO LAYOUT [NO_LAYOUT] Valid room '{room.name}' has no complete layout under "
                "its blocked cells, fixed mats, and the no-four-corners rule."
            ),
            file=sys.stderr,
        )
        print(
            "Repair: Remove or rotate a fixed mat, unblock or reshape isolated cells, then rerun.",
            file=sys.stderr,
        )
        return 1
    try:
        write_solution(room, solution, output)
    except OutputExistsError:
        _print_error(
            CommandError(
                "OUTPUT_EXISTS",
                f"Output path already exists: {output}",
                "Choose a new --out path; TatamiFit does not overwrite user files.",
            )
        )
        return 2
    except OSError as error:
        _print_error(
            CommandError(
                "OUTPUT_IO_ERROR",
                f"Could not write output at {output}: {error}",
                "Check the parent path and permissions, then choose a new --out path.",
            )
        )
        return 2
    print(
        f"LAYOUT {room.name}: {len(solution.placements)} mats, retained "
        f"{solution.retained_count}/{len(room.preferred)} preferred placements."
    )
    print(f"JSON: {output / 'layout.json'}")
    print(f"SVG:  {output / 'layout.svg'}")
    print(f"TEXT: {output / 'layout.txt'}")
    return 0


def _print_error(error: CommandError | InputError) -> None:
    print(f"ERROR [{error.code}] {error}", file=sys.stderr)
    print(f"Repair: {error.repair}", file=sys.stderr)
