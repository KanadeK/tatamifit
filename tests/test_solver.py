from __future__ import annotations

from collections.abc import Iterator

from tatamifit.model import Placement, Room, parse_room
from tatamifit.solver import Solution, four_corner_points, solve


def room(
    width: int,
    height: int,
    *,
    blocked: list[dict[str, object]] | None = None,
    fixed: list[dict[str, object]] | None = None,
    preferred: list[dict[str, object]] | None = None,
) -> Room:
    return parse_room(
        {
            "schema_version": 1,
            "name": "Test room",
            "width": width,
            "height": height,
            "blocked": blocked or [],
            "fixed": fixed or [],
            "preferred": preferred or [],
        }
    )


def placement(x: int, y: int, orientation: str) -> dict[str, object]:
    return {"x": x, "y": y, "orientation": orientation}


def all_horizontal(width: int, height: int) -> list[dict[str, object]]:
    return [placement(x, y, "horizontal") for y in range(height) for x in range(0, width, 2)]


def test_four_corner_points_reports_every_cross_junction() -> None:
    test_room = room(4, 4)
    mats = tuple(Placement(x, y, "horizontal") for y in range(4) for x in (0, 2))

    assert four_corner_points(test_room, mats) == ((2, 1), (2, 2), (2, 3))


def test_four_corner_points_accepts_two_mat_junction() -> None:
    test_room = room(2, 2)
    mats = (Placement(0, 0, "horizontal"), Placement(0, 1, "horizontal"))

    assert four_corner_points(test_room, mats) == ()


def test_solve_returns_deterministic_complete_layout() -> None:
    test_room = room(2, 2)

    first = solve(test_room)
    second = solve(test_room)

    assert first == second
    assert first == Solution(
        placements=(Placement(0, 0, "horizontal"), Placement(0, 1, "horizontal")),
        retained_preferred=(),
        changed_preferred=(),
        search_nodes=3,
    )


def test_solve_honors_fixed_mat() -> None:
    test_room = room(2, 2, fixed=[placement(0, 0, "vertical")])

    solution = solve(test_room)

    assert solution is not None
    assert solution.placements == (
        Placement(0, 0, "vertical"),
        Placement(1, 0, "vertical"),
    )


def test_solve_returns_none_for_disconnected_usable_cells() -> None:
    test_room = room(2, 2, blocked=[{"x": 0, "y": 0}, {"x": 1, "y": 1}])

    assert solve(test_room) is None


def test_solve_rejects_completed_fixed_four_corner_violation() -> None:
    test_room = room(4, 4, fixed=all_horizontal(4, 4))

    assert solve(test_room) is None


def test_solve_maximizes_retained_preferred_mats_against_exhaustive_oracle() -> None:
    preferences = all_horizontal(4, 4)
    test_room = room(4, 4, preferred=preferences)
    preferred_set = set(test_room.preferred)
    valid_tilings = [
        tiling
        for tiling in _all_domino_tilings(test_room.usable_cells)
        if not _independent_four_corner_points(test_room, tiling)
    ]
    oracle_score = max(len(preferred_set.intersection(tiling)) for tiling in valid_tilings)

    solution = solve(test_room)

    assert solution is not None
    assert solution.retained_count == oracle_score
    assert solution.changed_count == len(preferences) - oracle_score
    assert not _independent_four_corner_points(test_room, solution.placements)
    assert set(solution.retained_preferred).isdisjoint(solution.changed_preferred)
    assert set(solution.retained_preferred) | set(solution.changed_preferred) == preferred_set


def test_solve_scores_fixed_mat_when_it_is_also_preferred() -> None:
    mat = placement(0, 0, "horizontal")
    test_room = room(2, 2, fixed=[mat], preferred=[mat, placement(0, 1, "horizontal")])

    solution = solve(test_room)

    assert solution is not None
    assert solution.retained_count == 2
    assert solution.changed_count == 0


def test_solve_matches_exhaustive_oracle_for_every_four_by_four_preference_layout() -> None:
    blank_room = room(4, 4)
    all_tilings = list(_all_domino_tilings(blank_room.usable_cells))
    valid_tilings = [
        tiling for tiling in all_tilings if not _independent_four_corner_points(blank_room, tiling)
    ]

    for preferred_tiling in all_tilings:
        preferred = [placement(mat.x, mat.y, mat.orientation) for mat in preferred_tiling]
        test_room = room(4, 4, preferred=preferred)
        oracle_score = max(
            len(set(preferred_tiling).intersection(valid_tiling)) for valid_tiling in valid_tilings
        )

        solution = solve(test_room)

        assert solution is not None
        assert solution.retained_count == oracle_score, preferred_tiling


def test_solve_handles_narrow_boundary_room() -> None:
    test_room = room(1, 8)

    solution = solve(test_room)

    assert solution is not None
    assert solution.placements == tuple(Placement(0, y, "vertical") for y in range(0, 8, 2))
    assert four_corner_points(test_room, solution.placements) == ()


def _all_domino_tilings(cells: frozenset[tuple[int, int]]) -> Iterator[tuple[Placement, ...]]:
    if not cells:
        yield ()
        return
    x, y = min(cells, key=lambda cell: (cell[1], cell[0]))
    for dx, dy, orientation in ((1, 0, "horizontal"), (0, 1, "vertical")):
        neighbor = (x + dx, y + dy)
        if neighbor not in cells:
            continue
        mat = Placement(x, y, orientation)  # type: ignore[arg-type]
        for rest in _all_domino_tilings(cells - {mat.cells[0], mat.cells[1]}):
            yield (mat, *rest)


def _independent_four_corner_points(
    test_room: Room, mats: tuple[Placement, ...]
) -> tuple[tuple[int, int], ...]:
    owner = {cell: index for index, mat in enumerate(mats) for cell in mat.cells}
    violations: list[tuple[int, int]] = []
    for y in range(1, test_room.height):
        for x in range(1, test_room.width):
            adjacent = ((x - 1, y - 1), (x, y - 1), (x - 1, y), (x, y))
            if (
                all(cell in owner for cell in adjacent)
                and len({owner[cell] for cell in adjacent}) == 4
            ):
                violations.append((x, y))
    return tuple(violations)
