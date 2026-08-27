# TatamiFit selection research

Research date: 2026-08-27.

## Local portfolio guard

The top-level directories under `D:\我的\GitHub` were enumerated before choosing a
project, and root README headings/descriptions were extracted. The portfolio already
contains large families of developer/release tools, construction BOQ tools, game and
replay diagnostics, stage logistics, music/media tooling, physical packing and routing,
food scheduling, printing, and textile/craft checks.

Targeted README searches for `tatami`, `tatami mat arrangement`, `four corners`, and
room-mat layout found no local project implementing this problem. Several superficially
attractive ideas were rejected because local projects already own their core:

- theatre quick-change scheduling overlaps CueProof's handlers, routes, state, and timed
  backstage-transition feasibility model;
- escape-room reset compilation is already RoomRearm;
- knitting material and SVG sewing checks are already SkeinPlan and StitchProof;
- generic room movement and collision planning are already SofaPilot and StageTraffic.

The new project is an independent repository at `D:\我的\GitHub\tatamifit`; the outer
aggregation directory is not its repository.

## Candidate comparison

Scores are 1-5 for problem clarity, differentiation, 60-second proof, v0.1 feasibility,
installation/searchability, and maintenance cost (higher is better; 30 maximum).

| Candidate | Domain and real flow | Score | Decision |
| --- | --- | ---: | --- |
| TatamiFit | Room grid + constraints -> exact mat layout -> SVG/JSON/text | 29 | Selected: clear rule, visible proof, low dependency and maintenance cost |
| DadoQueue | Woodworking operations + dependencies -> setup-minimizing cut order | 23 | Rejected: useful, but safe operation modeling needs substantially more machine context |
| RollBudget | Shot/take plan + film rolls -> magazine allocation and waste report | 21 | Rejected: without more format and production assumptions the v0.1 value is too thin |
| QuickChangeProof | Costume changes + crew/stations -> feasible transition plan | 14 | Rejected locally: core feasibility model substantially duplicates CueProof |

The woodworking searches included `woodworking dado cut sequence table saw fence setup
optimizer` and `woodworking cut list optimizer minimize machine setup changes`. The
closest READMEs, WoodworkingShop and CutStock, optimize material nesting and guillotine
cut plans rather than setup-state changes. The film searches included `film stock roll
shot allocation planner`, `35mm footage calculator shooting ratio`, and `film stock
inventory roll management`. CineSched owns shoot calendars and scene breakdowns;
filmfriend inventories film/camera/development state. Neither established a strong,
small roll-allocation contract, which is why that candidate was not selected.

## Problem basis

The narrow rule implemented in v0.1 is intentionally explicit: 1-by-2 mats cover usable
grid cells without overlap, and no interior point may be the meeting point of four
different mats. This matches the definition in Project Euler problem 256 and the
University of Victoria paper page "Counting fixed-height tatami tilings".

- https://projecteuler.net/problem=256
- https://webhome.cs.uvic.ca/~ruskey/Publications/Tatami/Tatami.html
- https://arxiv.org/abs/1103.3309

TatamiFit does not claim to encode every regional, ceremonial, architectural, sizing,
moisture, substrate, or installation rule. Users supply an abstract half-mat grid.

## Five closest public projects and concrete differences

The GitHub searches used multiple groups: `tatami layout solver`, `tatami four corners
tiling`, `tatami tilings enumeration code`, and `domino tiling irregular region solver
SVG CLI`. The following README or complete project description was opened, not inferred
from a result title alone.

| Neighbor | What its README/code says it does | TatamiFit's substantive difference |
| --- | --- | --- |
| [takehiko/tatami.rb](https://gist.github.com/takehiko/35a372005f08a9c825dc) | Ruby gist enumerating rectangular tatami arrangements and testing four-corner/full-section-line fitness | Versioned room files, blocked cells, fixed mats, preference-based repair, stable artifacts, packaged CLI, explicit exits and repair guidance |
| [davidmisiak/tiler](https://github.com/davidmisiak/tiler) | General polyomino CLI with backtracking, DLX, SAT, ILP, and MiniZinc backends | One zero-runtime tatami contract with a domain rule and retained-layout objective, not a multi-backend arbitrary-tile framework |
| [cemulate/polyomino-solver](https://github.com/cemulate/polyomino-solver) | Browser app fitting arbitrary polyominoes by Algorithm X | Headless/CI-friendly planner for indistinguishable 1-by-2 mats, fixed/preferred placements, and no-four-corner evidence |
| [brianberns/Pips](https://github.com/brianberns/Pips) | Solver for the NYT Pips puzzle using pip-value region constraints and domino inventory | Plans physical room cells without pip values or puzzle feeds; the constraint is mat junction geometry and repair retention |
| [roothch/TilingGallery](https://github.com/roothch/TilingGallery) | Rust CLI generating decorative Penrose and Pinwheel SVG tilings | Solves finite coverage feasibility and reports no-layout failures; SVG is evidence of a constrained room plan, not decorative generation |

This evidence supports differentiation, not a claim that no similar repository exists
anywhere on GitHub.

## Selected v0.1 boundary

TatamiFit will:

- read strict, versioned JSON describing a rectangular grid, blocked cells, fixed mats,
  and optional preferred placements from an existing layout;
- find a complete 1-by-2 covering with no four-mat junctions;
- maximize exactly retained preferred placements, then choose a stable deterministic
  tie-break;
- write `layout.json`, `layout.svg`, and `layout.txt` only after a layout is found;
- fail clearly for invalid input and separately for a valid but unsatisfiable room.

It will not support half mats, non-grid measurements, cutting, prices, ceremonial layout
classification, installation advice, cloud storage, accounts, telemetry, or a visual
editor in v0.1.
