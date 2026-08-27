# Contributing to TatamiFit

Thanks for helping keep TatamiFit small, inspectable, and useful.

## Set up and verify

```console
git clone https://github.com/KanadeK/tatamifit.git
cd tatamifit
uv sync --locked --all-groups
uv run --no-sync python scripts/check.py
```

The final command is the only acceptance command used locally and in CI. Do not skip or
weaken a failing check.

## Change discipline

- Open a focused issue or pull request for one user-visible problem.
- Add a failing behavior test before changing solver, model, renderer, or CLI logic.
- Keep runtime dependencies empty unless the standard library cannot meet a concrete
  accepted requirement.
- Preserve deterministic artifacts, stable error codes, and exit meanings.
- Do not expand TatamiFit into installation advice or claim cultural rules beyond the
  documented grid constraint without authoritative sources and an explicit spec change.
- Run the complete gate after the final code change and include the command result in the
  pull request.

By contributing, you agree that your contribution is licensed under the repository's
[MIT License](LICENSE).
