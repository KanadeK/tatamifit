# Changelog

All notable user-visible changes are recorded here.

## [0.1.1] - 2026-08-30

### Fixed

- Reject duplicate JSON object fields with an actionable `DUPLICATE_FIELD` error instead
  of silently using the last value.

## [0.1.0] - 2026-08-27

### Added

- Plan complete 1-by-2 mat layouts on rectangular grids with blocked cells.
- Enforce fixed mats and the no-four-corners tatami rule.
- Prefer an existing layout to minimize changed placements during repair.
- Emit deterministic JSON, SVG, and text evidence with actionable failures.
