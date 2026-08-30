from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from tatamifit.cli import main


def write_room(path: Path, **changes: object) -> Path:
    payload: dict[str, object] = {
        "schema_version": 1,
        "name": "Four-by-four repair",
        "width": 4,
        "height": 4,
        "blocked": [],
        "fixed": [],
        "preferred": [
            {"x": x, "y": y, "orientation": "horizontal"} for y in range(4) for x in (0, 2)
        ],
    }
    payload.update(changes)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def read_layout(output: Path) -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads((output / "layout.json").read_text(encoding="utf-8")),
    )


def test_plan_runs_real_input_solver_and_writes_three_agreeing_artifacts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = write_room(tmp_path / "room.json")
    output = tmp_path / "result"

    exit_code = main(["plan", str(source), "--out", str(output)])

    assert exit_code == 0
    assert {path.name for path in output.iterdir()} == {"layout.json", "layout.svg", "layout.txt"}
    layout = read_layout(output)
    assert layout["status"] == "layout_found"
    summary = cast(dict[str, object], layout["summary"])
    assert summary["mat_count"] == 8
    assert summary["preferred_count"] == 8
    assert 0 < cast(int, summary["retained_count"]) < 8
    placements = cast(list[dict[str, object]], layout["placements"])
    identifiers = {cast(str, placement["id"]) for placement in placements}
    svg = (output / "layout.svg").read_text(encoding="utf-8")
    text = (output / "layout.txt").read_text(encoding="utf-8")
    assert identifiers == {f"M{index:02d}" for index in range(1, 9)}
    assert all(identifier in svg and identifier in text for identifier in identifiers)
    assert "four different mats meet" in svg
    captured = capsys.readouterr()
    assert "LAYOUT Four-by-four repair" in captured.out
    assert "retained" in captured.out
    assert captured.err == ""


def test_plan_is_byte_deterministic(tmp_path: Path) -> None:
    source = write_room(tmp_path / "room.json")
    first = tmp_path / "first"
    second = tmp_path / "second"

    assert main(["plan", str(source), "--out", str(first)]) == 0
    assert main(["plan", str(source), "--out", str(second)]) == 0

    for name in ("layout.json", "layout.svg", "layout.txt"):
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_plan_returns_one_and_writes_nothing_when_valid_room_has_no_layout(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = write_room(
        tmp_path / "no-layout.json",
        width=2,
        height=2,
        blocked=[{"x": 0, "y": 0}, {"x": 1, "y": 1}],
        preferred=[],
    )
    output = tmp_path / "should-not-exist"

    exit_code = main(["plan", str(source), "--out", str(output)])

    assert exit_code == 1
    assert not output.exists()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "NO LAYOUT [NO_LAYOUT]" in captured.err
    assert "Repair:" in captured.err


def test_plan_returns_two_and_writes_nothing_for_invalid_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "invalid.json"
    source.write_text('{"schema_version": 1,', encoding="utf-8")
    output = tmp_path / "should-not-exist"

    exit_code = main(["plan", str(source), "--out", str(output)])

    assert exit_code == 2
    assert not output.exists()
    captured = capsys.readouterr()
    assert "ERROR [INVALID_JSON]" in captured.err
    assert "line 1" in captured.err
    assert "Repair:" in captured.err


def test_plan_rejects_duplicate_json_field(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "duplicate.json"
    source.write_text(
        '{"schema_version":1,"name":"Duplicate width","width":4,"width":2,'
        '"height":2,"blocked":[],"fixed":[],"preferred":[]}',
        encoding="utf-8",
    )
    output = tmp_path / "should-not-exist"

    exit_code = main(["plan", str(source), "--out", str(output)])

    assert exit_code == 2
    assert not output.exists()
    captured = capsys.readouterr()
    assert "ERROR [DUPLICATE_FIELD]" in captured.err
    assert "'width'" in captured.err
    assert "Remove one duplicate field" in captured.err


def test_plan_returns_two_for_missing_input_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "missing.json"
    output = tmp_path / "should-not-exist"

    exit_code = main(["plan", str(source), "--out", str(output)])

    assert exit_code == 2
    assert not output.exists()
    captured = capsys.readouterr()
    assert f"ERROR [INPUT_NOT_FOUND] Input file does not exist: {source}" in captured.err
    assert "Check the input path" in captured.err


def test_plan_preserves_existing_output_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = write_room(tmp_path / "room.json")
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("owned by user", encoding="utf-8")

    exit_code = main(["plan", str(source), "--out", str(output)])

    assert exit_code == 2
    assert sentinel.read_text(encoding="utf-8") == "owned by user"
    assert {path.name for path in output.iterdir()} == {"keep.txt"}
    captured = capsys.readouterr()
    assert f"ERROR [OUTPUT_EXISTS] Output path already exists: {output}" in captured.err
    assert "Choose a new --out path" in captured.err


def test_demo_processes_bundled_input_through_the_real_solver(tmp_path: Path) -> None:
    output = tmp_path / "demo"

    exit_code = main(["demo", "--out", str(output)])

    assert exit_code == 0
    layout = read_layout(output)
    assert layout["status"] == "layout_found"
    assert layout["room"] == {
        "name": "TatamiFit repair demo",
        "width": 4,
        "height": 4,
        "blocked": [],
    }
