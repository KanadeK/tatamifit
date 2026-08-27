"""Strict external input model for TatamiFit rooms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

Cell = tuple[int, int]
Orientation = Literal["horizontal", "vertical"]


class InputError(ValueError):
    """A stable, user-repairable room input error."""

    def __init__(self, code: str, message: str, repair: str) -> None:
        super().__init__(message)
        self.code = code
        self.repair = repair


@dataclass(frozen=True, order=True)
class Placement:
    """One 1-by-2 mat, anchored at its top-left cell."""

    x: int
    y: int
    orientation: Orientation

    @property
    def cells(self) -> tuple[Cell, Cell]:
        if self.orientation == "horizontal":
            return ((self.x, self.y), (self.x + 1, self.y))
        return ((self.x, self.y), (self.x, self.y + 1))


@dataclass(frozen=True)
class Room:
    """Validated room contract consumed by the solver."""

    name: str
    width: int
    height: int
    blocked: frozenset[Cell]
    fixed: tuple[Placement, ...]
    preferred: tuple[Placement, ...]

    @property
    def usable_cells(self) -> frozenset[Cell]:
        return frozenset(
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in self.blocked
        )


ROOT_FIELDS = frozenset(
    {"schema_version", "name", "width", "height", "blocked", "fixed", "preferred"}
)
REQUIRED_FIELDS = ("schema_version", "name", "width", "height")


def parse_room(value: object) -> Room:
    """Validate untrusted decoded JSON and return an immutable room."""

    root = _mapping(value, "root")
    unknown = set(root) - ROOT_FIELDS
    if unknown:
        field = sorted(unknown)[0]
        raise InputError(
            "UNKNOWN_FIELD",
            f"Unknown field '{field}'.",
            f"Remove or correct '{field}'; allowed fields are {', '.join(sorted(ROOT_FIELDS))}.",
        )
    for field in REQUIRED_FIELDS:
        if field not in root:
            raise InputError(
                "MISSING_FIELD",
                f"Missing required field '{field}'.",
                f"Add '{field}' to the root object.",
            )

    schema_version = _integer(root["schema_version"], "schema_version")
    if schema_version != 1:
        raise InputError(
            "UNSUPPORTED_SCHEMA",
            f"schema_version must be 1, got {schema_version}.",
            "Set schema_version to 1 and follow the v1 input contract.",
        )

    name_value = root["name"]
    if not isinstance(name_value, str):
        raise InputError(
            "INVALID_TYPE", "name must be a string.", "Set name to a non-empty JSON string."
        )
    name = name_value.strip()
    if not name:
        raise InputError(
            "INVALID_NAME", "name must not be blank.", "Give the room a non-empty name."
        )

    width = _dimension(root["width"], "width")
    height = _dimension(root["height"], "height")
    blocked = _blocked_cells(root.get("blocked", []), width, height)
    usable_count = width * height - len(blocked)
    if usable_count % 2:
        raise InputError(
            "ODD_USABLE_AREA",
            f"The room has {usable_count} usable cells; 1-by-2 mats require an even count.",
            "Block or unblock one cell so the usable-cell count is even.",
        )
    if usable_count > 64:
        raise InputError(
            "SEARCH_LIMIT",
            f"The room has {usable_count} usable cells; v0.1 supports at most 64.",
            "Split the room into independently planned regions of 64 usable cells or fewer.",
        )

    fixed = _placements(root.get("fixed", []), "fixed", width, height, blocked)
    preferred = _placements(root.get("preferred", []), "preferred", width, height, blocked)
    return Room(name, width, height, blocked, fixed, preferred)


def _mapping(value: object, path: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise InputError(
            "INVALID_TYPE", f"{path} must be a JSON object.", f"Set {path} to a JSON object."
        )
    return cast(dict[str, object], value)


def _integer(value: object, path: str) -> int:
    if type(value) is not int:
        raise InputError(
            "INVALID_TYPE", f"{path} must be an integer.", f"Set {path} to a JSON integer."
        )
    return value


def _dimension(value: object, path: str) -> int:
    dimension = _integer(value, path)
    if dimension < 1:
        raise InputError(
            "INVALID_DIMENSION", f"{path} must be at least 1.", f"Set {path} between 1 and 20."
        )
    if dimension > 20:
        raise InputError(
            "GRID_TOO_LARGE",
            f"{path} is {dimension}; v0.1 allows at most 20.",
            f"Set {path} to 20 or less.",
        )
    return dimension


def _items(value: object, path: str) -> list[object]:
    if not isinstance(value, list):
        raise InputError(
            "INVALID_TYPE", f"{path} must be a JSON array.", f"Set {path} to a JSON array."
        )
    return cast(list[object], value)


def _blocked_cells(value: object, width: int, height: int) -> frozenset[Cell]:
    blocked: set[Cell] = set()
    for index, item in enumerate(_items(value, "blocked")):
        path = f"blocked[{index}]"
        mapping = _mapping(item, path)
        _check_fields(mapping, path, frozenset({"x", "y"}))
        cell = (_required_integer(mapping, path, "x"), _required_integer(mapping, path, "y"))
        if not _inside(cell, width, height):
            raise InputError(
                "CELL_OUT_OF_BOUNDS",
                f"{path} cell {cell} is outside the {width}x{height} grid.",
                f"Move {path} inside x=0..{width - 1}, y=0..{height - 1}.",
            )
        if cell in blocked:
            raise InputError(
                "DUPLICATE_BLOCKED_CELL",
                f"{path} repeats blocked cell {cell}.",
                f"Remove the duplicate {path} entry.",
            )
        blocked.add(cell)
    return frozenset(blocked)


def _placements(
    value: object,
    path: Literal["fixed", "preferred"],
    width: int,
    height: int,
    blocked: frozenset[Cell],
) -> tuple[Placement, ...]:
    placements: list[Placement] = []
    occupied: set[Cell] = set()
    for index, item in enumerate(_items(value, path)):
        item_path = f"{path}[{index}]"
        mapping = _mapping(item, item_path)
        _check_fields(mapping, item_path, frozenset({"x", "y", "orientation"}))
        x = _required_integer(mapping, item_path, "x")
        y = _required_integer(mapping, item_path, "y")
        if "orientation" not in mapping:
            raise InputError(
                "MISSING_FIELD",
                f"Missing required field '{item_path}.orientation'.",
                f"Add '{item_path}.orientation' as 'horizontal' or 'vertical'.",
            )
        orientation_value = mapping["orientation"]
        if orientation_value not in ("horizontal", "vertical"):
            raise InputError(
                "INVALID_ORIENTATION",
                f"{item_path}.orientation must be 'horizontal' or 'vertical'.",
                f"Set {item_path}.orientation to 'horizontal' or 'vertical'.",
            )
        placement = Placement(x, y, orientation_value)
        if any(not _inside(cell, width, height) for cell in placement.cells):
            raise InputError(
                "MAT_OUT_OF_BOUNDS",
                f"{item_path} extends outside the {width}x{height} grid.",
                f"Move or rotate {item_path} so both cells are inside the grid.",
            )
        if any(cell in blocked for cell in placement.cells):
            label = "FIXED_ON_BLOCKED_CELL" if path == "fixed" else "PREFERRED_ON_BLOCKED_CELL"
            raise InputError(
                label,
                f"{item_path} covers a blocked cell.",
                f"Move {item_path} or remove the conflicting blocked cell.",
            )
        overlap = occupied.intersection(placement.cells)
        if overlap:
            label = "FIXED_MATS_OVERLAP" if path == "fixed" else "PREFERRED_MATS_OVERLAP"
            raise InputError(
                label,
                f"{item_path} overlaps an earlier {path} mat at {sorted(overlap)[0]}.",
                f"Move or remove {item_path} so {path} mats do not overlap.",
            )
        placements.append(placement)
        occupied.update(placement.cells)
    return tuple(placements)


def _check_fields(mapping: dict[str, object], path: str, allowed: frozenset[str]) -> None:
    unknown = set(mapping) - allowed
    if unknown:
        field = sorted(unknown)[0]
        full_path = f"{path}.{field}"
        raise InputError(
            "UNKNOWN_FIELD",
            f"Unknown field '{full_path}'.",
            f"Remove or correct '{full_path}'.",
        )


def _required_integer(mapping: dict[str, object], path: str, field: str) -> int:
    if field not in mapping:
        full_path = f"{path}.{field}"
        raise InputError(
            "MISSING_FIELD",
            f"Missing required field '{full_path}'.",
            f"Add '{full_path}' as an integer.",
        )
    return _integer(mapping[field], f"{path}.{field}")


def _inside(cell: Cell, width: int, height: int) -> bool:
    x, y = cell
    return 0 <= x < width and 0 <= y < height
