from __future__ import annotations

from copy import deepcopy

import pytest

from tatamifit.model import InputError, Placement, parse_room

VALID_ROOM: dict[str, object] = {
    "schema_version": 1,
    "name": "Repair room",
    "width": 4,
    "height": 4,
    "blocked": [],
    "fixed": [{"x": 0, "y": 0, "orientation": "horizontal"}],
    "preferred": [
        {"x": 0, "y": 0, "orientation": "horizontal"},
        {"x": 2, "y": 0, "orientation": "horizontal"},
    ],
}


def changed(**values: object) -> dict[str, object]:
    room = deepcopy(VALID_ROOM)
    room.update(values)
    return room


def test_parse_room_returns_typed_immutable_contract() -> None:
    room = parse_room(VALID_ROOM)

    assert room.name == "Repair room"
    assert room.width == 4
    assert room.height == 4
    assert room.usable_cells == frozenset((x, y) for y in range(4) for x in range(4))
    assert room.fixed == (Placement(0, 0, "horizontal"),)
    assert room.preferred[1].cells == ((2, 0), (3, 0))


@pytest.mark.parametrize("field", ["schema_version", "name", "width", "height"])
def test_parse_room_requires_every_scalar_field(field: str) -> None:
    payload = deepcopy(VALID_ROOM)
    del payload[field]

    with pytest.raises(InputError) as raised:
        parse_room(payload)

    assert raised.value.code == "MISSING_FIELD"
    assert field in str(raised.value)
    assert raised.value.repair.startswith("Add")


def test_parse_room_rejects_unknown_root_key() -> None:
    with pytest.raises(InputError) as raised:
        parse_room(changed(heigth=4))

    assert raised.value.code == "UNKNOWN_FIELD"
    assert "heigth" in str(raised.value)
    assert "Remove or correct" in raised.value.repair


@pytest.mark.parametrize(
    ("values", "code"),
    [
        ({"schema_version": 2}, "UNSUPPORTED_SCHEMA"),
        ({"width": True}, "INVALID_TYPE"),
        ({"width": 0}, "INVALID_DIMENSION"),
        ({"width": 21}, "GRID_TOO_LARGE"),
        ({"name": "  "}, "INVALID_NAME"),
    ],
)
def test_parse_room_rejects_invalid_scalars(values: dict[str, object], code: str) -> None:
    with pytest.raises(InputError) as raised:
        parse_room(changed(**values))

    assert raised.value.code == code
    assert raised.value.repair


def test_parse_room_rejects_unknown_placement_field() -> None:
    preferred = [{"x": 0, "y": 0, "orientation": "horizontal", "keep": True}]

    with pytest.raises(InputError) as raised:
        parse_room(changed(preferred=preferred))

    assert raised.value.code == "UNKNOWN_FIELD"
    assert "preferred[0].keep" in str(raised.value)


def test_parse_room_rejects_blocked_cell_outside_grid() -> None:
    with pytest.raises(InputError) as raised:
        parse_room(changed(blocked=[{"x": 4, "y": 0}]))

    assert raised.value.code == "CELL_OUT_OF_BOUNDS"
    assert "blocked[0]" in str(raised.value)


def test_parse_room_rejects_duplicate_blocked_cell() -> None:
    blocked = [{"x": 3, "y": 3}, {"x": 3, "y": 3}]

    with pytest.raises(InputError) as raised:
        parse_room(changed(blocked=blocked))

    assert raised.value.code == "DUPLICATE_BLOCKED_CELL"


def test_parse_room_rejects_odd_usable_area() -> None:
    with pytest.raises(InputError) as raised:
        parse_room(changed(blocked=[{"x": 3, "y": 3}]))

    assert raised.value.code == "ODD_USABLE_AREA"
    assert "block or unblock one cell" in raised.value.repair.lower()


def test_parse_room_rejects_more_than_sixty_four_usable_cells() -> None:
    with pytest.raises(InputError) as raised:
        parse_room(changed(width=10, height=8, fixed=[], preferred=[]))

    assert raised.value.code == "SEARCH_LIMIT"
    assert "64" in str(raised.value)


def test_parse_room_rejects_fixed_mat_on_blocked_cell() -> None:
    blocked = [{"x": 0, "y": 0}, {"x": 3, "y": 3}]

    with pytest.raises(InputError) as raised:
        parse_room(changed(blocked=blocked))

    assert raised.value.code == "FIXED_ON_BLOCKED_CELL"


def test_parse_room_rejects_overlapping_fixed_mats() -> None:
    fixed = [
        {"x": 0, "y": 0, "orientation": "horizontal"},
        {"x": 1, "y": 0, "orientation": "vertical"},
    ]

    with pytest.raises(InputError) as raised:
        parse_room(changed(fixed=fixed))

    assert raised.value.code == "FIXED_MATS_OVERLAP"
    assert "fixed[1]" in str(raised.value)


def test_parse_room_rejects_overlapping_preferred_mats() -> None:
    preferred = [
        {"x": 0, "y": 0, "orientation": "horizontal"},
        {"x": 1, "y": 0, "orientation": "vertical"},
    ]

    with pytest.raises(InputError) as raised:
        parse_room(changed(preferred=preferred))

    assert raised.value.code == "PREFERRED_MATS_OVERLAP"


def test_parse_room_rejects_placement_that_runs_past_grid() -> None:
    fixed = [{"x": 3, "y": 0, "orientation": "horizontal"}]

    with pytest.raises(InputError) as raised:
        parse_room(changed(fixed=fixed))

    assert raised.value.code == "MAT_OUT_OF_BOUNDS"
    assert "fixed[0]" in str(raised.value)
