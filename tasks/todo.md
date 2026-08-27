# TatamiFit v0.1.0 tasks

## Contract and model

- [x] Add `pyproject.toml`, package skeleton, and locked dev environment.
  - Acceptance: import target and test discovery exist without implementation behavior.
  - Verify: the first model test fails for the expected missing behavior.
  - Files: `pyproject.toml`, `src/tatamifit/__init__.py`, `tests/test_model.py`.
- [x] Implement strict room parsing and placement validation.
  - Acceptance: valid input becomes typed immutable data; malformed boundaries have stable
    codes and repair text.
  - Verify: focused model tests, Ruff, and mypy pass.
  - Files: `src/tatamifit/model.py`, `tests/test_model.py`.

## Solver

- [x] Implement legal placements and the no-four-corners rule test-first.
  - Acceptance: fixed placements are honored and every completed vertex is valid.
  - Verify: focused solver rule tests pass.
  - Files: `src/tatamifit/solver.py`, `tests/test_solver.py`.
- [x] Implement preference-maximizing exact search and deterministic no-layout result.
  - Acceptance: small exhaustive oracle cases agree; valid unsatisfiable input returns none.
  - Verify: full solver tests pass with no skipped cases.
  - Files: `src/tatamifit/solver.py`, `tests/test_solver.py`.

## Product path

- [ ] Implement deterministic JSON/SVG/text renderers and atomic CLI output.
  - Acceptance: success writes three agreeing files; exit 1/2 writes no output directory.
  - Verify: CLI integration tests execute the real parser, solver, and filesystem.
  - Files: `src/tatamifit/render.py`, `src/tatamifit/cli.py`, `tests/test_cli.py`.
- [ ] Add examples, README, CI, and the single local/release gate.
  - Acceptance: all documented primary commands are exercised by the gate.
  - Verify: `uv run python scripts/check.py` passes, including clean wheel install.
  - Files: `examples/*`, `README.md`, `scripts/check.py`, `.github/workflows/ci.yml`.

## Review and release

- [ ] Review final diff for correctness, simplicity, architecture, security, and bounded
  performance; repair required findings.
  - Verify: complete gate passes after the final code change and worktree is clean.
- [ ] Publish main, verify CI/contributors, tag `v0.1.0`, and publish wheel/sdist Release.
  - Verify: public GitHub API and remote refs agree on commit, tag, release, and assets.
- [ ] Re-download the Release wheel into a clean environment and run the real repair
  example; verify anonymous access and send Gmail.
  - Verify: installed artifacts are valid, URLs work without auth, and Gmail reports sent.
