# Implementation plan: TatamiFit v0.1.0

## Overview

Build a zero-runtime-dependency Python CLI in thin tested slices, then use one local/CI
gate and close the complete remote release loop. No implementation step changes the
outer `D:\我的\GitHub` repository.

## Dependency graph

```text
strict room model
    -> legal placement geometry
        -> exact constrained solver
            -> deterministic renderers
                -> CLI and failure contract
                    -> package/install gate
                        -> GitHub CI and Release proof
```

## Architecture decisions

- Use direct backtracking with local pruning because v0.1 has one tile shape and one
  junction rule; a generic SAT/DLX dependency would add maintenance without user value.
- Treat preferred placements as an optimization score and fixed placements as hard.
- Render from the solved placement list so JSON, SVG, and text share one source of truth.
- Write artifacts to a temporary sibling and rename only after all renders succeed.

## Phases and checkpoints

### Phase 1: contract and model

- Task 1: create packaging/test scaffolding and failing model tests.
- Task 2: implement strict parsing and placement validation.

Checkpoint: focused model tests, Ruff, and mypy pass.

### Phase 2: real solver

- Task 3: add failing rule/solver tests, then implement exact search and preference score.
- Task 4: add unsatisfiable, fixed-mat, and deterministic boundary coverage.

Checkpoint: solver suite passes and examples can be solved in-process.

### Phase 3: product path

- Task 5: add failing CLI/output tests, then implement renderers and commands.
- Task 6: add fixtures, README, CI, and the single clean-install gate.

Checkpoint: `uv run python scripts/check.py` passes from a clean checkout state.

### Phase 4: release

- Task 7: review final diff on five axes, fix findings, rerun the gate, and merge to main.
- Task 8: publish, wait for CI, create annotated tag and formal Release with wheel/sdist.
- Task 9: download remote wheel, install/run in a new environment, verify anonymous URLs,
  send Gmail, and only then close the goal.

## Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Exponential search on pathological rooms | Slow or misleading CLI | Honest 64-cell limit, most-constrained-cell choice, local rule pruning, documented boundary |
| Preference optimization stops too early | Non-minimal repair | Branch-and-bound oracle tests on small rooms and exhaustive test comparison |
| Render artifacts disagree | False visual evidence | Generate every format from one immutable solved placement tuple and integration-compare |
| GitHub authentication remains invalid | Remote steps blocked | Finish all local work first, then request only the official login action if still required |
| CI differs from local | False local confidence | CI invokes the exact `scripts/check.py` command used locally |

## Open questions

None that change v0.1 scope.
