# Spec: TatamiFit v0.1.0

## Assumptions

1. The useful minimal model is an equal-cell grid where every mat covers exactly two
   orthogonally adjacent cells.
2. The only cultural/layout rule claimed by the program is that four different mats do
   not meet at one point.
3. A preferred placement is a repair objective, not a hard constraint; a fixed placement
   is hard.
4. The GitHub owner will be the account confirmed by `gh auth status` before publication.
5. MIT is appropriate because the implementation is original and uses no copied solver
   code or runtime dependency.

## Objective

TatamiFit is an offline command-line planner for people prototyping or repairing modular
tatami-style 1-by-2 mat layouts. A user supplies a real room-grid file. The program
validates it, searches actual placements, enforces fixed mats and the no-four-corners
rule, prefers unchanged placements, and produces independently inspectable artifacts.

The core user story is: "Given this usable floor grid and the mats I must or would like
to retain, show one valid layout or tell me exactly why the request cannot be processed."

## Tech stack

- Python 3.11 or newer.
- Python standard library only at runtime.
- `pytest`, `pytest-cov`, Ruff, mypy, and `build` as locked development tools.
- `hatchling` build backend; wheel and source distribution release assets.
- GitHub Actions calling the same repository gate as local development.

## Commands

```console
uv sync --locked --all-groups
uv run tatamifit plan examples/repair-room.json --out build/repair-room
uv run tatamifit demo --out build/demo
uv run python scripts/check.py
uv build
```

Installed release proof:

```console
python -m pip install tatamifit-0.1.0-py3-none-any.whl
tatamifit plan repair-room.json --out result
```

## Project structure

```text
src/tatamifit/     package, input model, solver, renderers, CLI
tests/             unit and CLI integration tests
examples/          success, boundary, unsatisfiable, and invalid inputs
docs/              research and product specification
tasks/             implementation plan and live checklist
scripts/check.py   single local/CI/release acceptance command
.github/workflows/ continuous integration
```

## Input contract

The root object is strict and versioned:

```json
{
  "schema_version": 1,
  "name": "Four-by-four repair",
  "width": 4,
  "height": 4,
  "blocked": [],
  "fixed": [{"x": 0, "y": 0, "orientation": "horizontal"}],
  "preferred": [{"x": 0, "y": 0, "orientation": "horizontal"}]
}
```

Coordinates are zero-based. `horizontal` covers `(x,y)` and `(x+1,y)`; `vertical`
covers `(x,y)` and `(x,y+1)`. Unknown keys, invalid types, out-of-bounds cells,
overlapping fixed mats, and odd usable area are input errors. v0.1 limits the grid to
20 by 20 and 64 usable cells so the exact search has an honest operating boundary.

## Output and exits

- Exit `0`: a layout was found and all three artifacts were committed to the requested
  output directory.
- Exit `1`: input was valid but no layout exists under the hard room/fixed constraints.
- Exit `2`: malformed input, I/O, or CLI usage. The message includes a stable code and a
  user-executable repair direction.

No output directory is created for exit `1` or `2`.

`layout.json` is the stable machine contract. `layout.svg` is a standalone visual plan.
`layout.txt` is a terminal/printable cell map and summary. Artifact order, mat IDs, and
JSON serialization are deterministic.

## Core algorithm

Use exact backtracking over domino placements:

1. Validate and place hard fixed mats.
2. Select the uncovered usable cell with the fewest legal candidate placements.
3. Try preferred candidates first, then a stable coordinate/orientation order.
4. Reject a partial branch as soon as a fully covered vertex has four distinct mats.
5. Track retained preferred placements and prune branches whose best possible score
   cannot beat the current solution.
6. Stop at the theoretical preference maximum; otherwise return the best stable layout.

The implementation favors transparent correctness over a generic exact-cover framework.

## Code style

Use typed dataclasses and pure functions for the model and solver. Validate only at file
and CLI boundaries; internal functions rely on validated invariants and fail fast.

```python
def solve(room: Room) -> Solution | None:
    state = SearchState.from_room(room)
    return search(state)
```

Names describe domain concepts (`blocked_cells`, `retained_preferred`), exceptions carry
stable external error codes, and no one-use abstraction is introduced.

## Testing strategy

- Unit tests: strict parsing, placement geometry, four-corner detection, preference
  optimization, deterministic tie-breaks, and unsatisfiable shapes.
- Integration tests: CLI success, boundary success, valid-no-layout, malformed input,
  atomic output behavior, and installed entry point.
- Coverage gate: at least 90% branch coverage for `src/tatamifit`.
- Packaging gate: build wheel/sdist, install the wheel in a fresh virtual environment,
  invoke the installed console script on real examples, and inspect outputs.
- No mocks for the solver, filesystem, subprocess, package install, or CLI flows.

## Boundaries

Always:

- keep runtime dependency-free and outputs deterministic;
- validate untrusted JSON before solver entry;
- preserve the distinction between invalid input and a valid unsatisfiable room;
- run `uv run python scripts/check.py` before release commits and tags.

Requires new user scope:

- publishing to PyPI or another package registry;
- adding network access, telemetry, accounts, a hosted service, or a GUI;
- claiming regional/ceremonial/installation correctness beyond the stated grid rule.

Never:

- commit credentials or generated virtual environments;
- silently relax fixed mats or the no-four-corners rule;
- create partial user output after a failed plan;
- describe the output as a professional installation or structural guarantee.

## Success criteria

1. Success, boundary, no-layout, and invalid fixtures produce their documented exits and
   messages.
2. A preference repair fixture proves the selected layout retains the maximum possible
   existing placements and has no four-mat junction.
3. JSON, SVG, and text artifacts are deterministic and agree on every mat placement.
4. The single gate proves formatting, lint, strict types, unit/integration coverage,
   package build, clean wheel install, installed CLI execution, and README quick start.
5. README documents problem, users, installation, 60-second proof, input/output, limits,
   exits, and troubleshooting.
6. Public GitHub main, CI, tag, formal Release, wheel/sdist assets, remote clean install,
   anonymous repository/Release access, correct contributor identity, and Gmail delivery
   all have current evidence before the goal is marked complete.

## Open questions

None for v0.1. Candidate features outside the selected boundary are intentionally not
decided.
