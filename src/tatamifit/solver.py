"""Exact no-four-corners layout search."""

from __future__ import annotations

from dataclasses import dataclass

from tatamifit.model import Cell, Placement, Room

ORIENTATION_ORDER = {"horizontal": 0, "vertical": 1}


@dataclass(frozen=True)
class Solution:
    """One complete deterministic layout and its repair score."""

    placements: tuple[Placement, ...]
    retained_preferred: tuple[Placement, ...]
    changed_preferred: tuple[Placement, ...]
    search_nodes: int

    @property
    def retained_count(self) -> int:
        return len(self.retained_preferred)

    @property
    def changed_count(self) -> int:
        return len(self.changed_preferred)


def four_corner_points(room: Room, placements: tuple[Placement, ...]) -> tuple[Cell, ...]:
    """Return interior vertices where four different mats meet."""

    owner = {cell: index for index, placement in enumerate(placements) for cell in placement.cells}
    violations: list[Cell] = []
    for y in range(1, room.height):
        for x in range(1, room.width):
            adjacent = ((x - 1, y - 1), (x, y - 1), (x - 1, y), (x, y))
            if (
                all(cell in owner for cell in adjacent)
                and len({owner[cell] for cell in adjacent}) == 4
            ):
                violations.append((x, y))
    return tuple(violations)


def solve(room: Room) -> Solution | None:
    """Find the layout retaining the most preferred placements, if one exists."""

    placements = list(room.fixed)
    placement_set = set(placements)
    occupied = {cell for placement in placements for cell in placement.cells}
    if four_corner_points(room, tuple(placements)):
        return None

    uncovered = set(room.usable_cells - occupied)
    preferred_set = set(room.preferred)
    retained = len(placement_set & preferred_set)
    theoretical_max = retained + sum(
        placement not in placement_set and all(cell in uncovered for cell in placement.cells)
        for placement in room.preferred
    )
    best: tuple[Placement, ...] | None = None
    best_score = -1
    search_nodes = 0

    def search(score: int) -> bool:
        nonlocal best, best_score, search_nodes
        search_nodes += 1
        if not uncovered:
            if score > best_score:
                best = tuple(sorted(placements, key=_placement_key))
                best_score = score
            return score == theoretical_max

        optimistic_score = score + sum(
            placement not in placement_set and all(cell in uncovered for cell in placement.cells)
            for placement in room.preferred
        )
        if optimistic_score < best_score:
            return False

        candidate_lists = [(_legal_placements(cell, uncovered), cell) for cell in uncovered]
        candidates, _ = min(
            candidate_lists, key=lambda item: (len(item[0]), item[1][1], item[1][0])
        )
        if not candidates:
            return False
        candidates.sort(
            key=lambda placement: (placement not in preferred_set, *_placement_key(placement))
        )
        for placement in candidates:
            placements.append(placement)
            placement_set.add(placement)
            uncovered.difference_update(placement.cells)
            if not four_corner_points(room, tuple(placements)):
                reached_maximum = search(score + (placement in preferred_set))
                if reached_maximum:
                    return True
            uncovered.update(placement.cells)
            placement_set.remove(placement)
            placements.pop()
        return False

    search(retained)
    if best is None:
        return None
    best_set = set(best)
    retained_preferred = tuple(placement for placement in room.preferred if placement in best_set)
    changed_preferred = tuple(
        placement for placement in room.preferred if placement not in best_set
    )
    return Solution(best, retained_preferred, changed_preferred, search_nodes)


def _legal_placements(cell: Cell, uncovered: set[Cell]) -> list[Placement]:
    x, y = cell
    candidates = (
        (Placement(x - 1, y, "horizontal"), (x - 1, y)),
        (Placement(x, y, "horizontal"), (x + 1, y)),
        (Placement(x, y - 1, "vertical"), (x, y - 1)),
        (Placement(x, y, "vertical"), (x, y + 1)),
    )
    return [placement for placement, neighbor in candidates if neighbor in uncovered]


def _placement_key(placement: Placement) -> tuple[int, int, int]:
    return (placement.y, placement.x, ORIENTATION_ORDER[placement.orientation])
