# Changelog

All notable changes to this project are documented in this file. Format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.5.0] - 2026-07-07

### Added

- New `step-reminders` sub-skill: builds a step-by-step clock-time timeline
  (`scripts/timeline.py`, forward-scheduling counterpart to
  `calculate-fermentation-schedule`'s backward scheduling) from a start time
  and ordered step durations, always anchored to the real system clock
  (`scripts/now.py`) rather than the model's guess of "now". Optionally sets
  up active reminders via the host's `/schedule` skill (`CronCreate`) for
  steps ≥ 15 minutes, with explicit user confirmation before creating each
  scheduled run, and a graceful static-timeline-only fallback when the host
  doesn't support scheduling.
- `dough-recipe` orchestrator now asks, after presenting the recipe, whether
  the user wants a timeline and reminders (two separate asks: timeline first,
  active reminders as its own follow-up).

## [0.4.0] - 2026-07-06

### Changed

- `dough-recipe` orchestrator now asks upfront for salt level, oil/fat level,
  and predough choice (previously silently defaulted/inferred), alongside
  purpose/portions/temperature, as one combined question. Salt and oil each
  accept a quick none/low/normal/high pick (mapped to fixed percentages —
  see `calculate-bakers-percentage`'s SKILL.md) or an exact percent/gram
  amount. Documented the two-pass grams-to-percent conversion needed when
  the user gives an absolute gram amount instead of a percent, since that
  conversion depends on flour weight, which depends on the percentages.

## [0.3.0] - 2026-07-06

### Changed

- `dough-recipe` orchestrator now asks for the ambient/dough temperature
  whenever a fermentation time is in play (duration, ready-by time, or
  predough timing), instead of silently assuming room temperature — every
  5°C roughly doubles or halves the required yeast %.
- Refined the fermentation-style default: "direct"/same-day style is now only
  picked when the user names a style explicitly, not inferred from urgency
  language alone. Found via live use that stacking "direct" mode on an
  already-short explicit fermentation time double-counts speed (4h at 21°C +
  direct mode produced 5.9% yeast, outside fresh yeast's realistic 3%
  ceiling); neapolitan is now the baseline unless a style is named.

## [0.2.0] - 2026-07-06

### Changed

- Restructured from a single `dough-recipe` skill into an orchestrator +
  four standalone sub-skills, each independently triggerable and
  independently installable:
  - `skills/dough-recipe` (orchestrator — Q&A + chaining, no calculation logic)
  - `skills/calculate-bakers-percentage` (flour/water/salt/sugar/fat)
  - `skills/calculate-yeast` (time/temperature → yeast %)
  - `skills/calculate-predough` (poolish/biga split + main-dough reduction)
  - `skills/calculate-fermentation-schedule` (ready-by-time scheduling)
- Moved the `skills` field from `plugin.json` to `marketplace.json`'s plugin
  entry, matching the convention used by other real marketplace repos
  (`academic-research-skills`, `claude-plugin-product-management`).

### Added

- `CHANGELOG.md`, `CLAUDE.md`.

## [0.1.0] - 2026-07-06

### Added

- Initial single-skill `dough-recipe` plugin: one `SKILL.md` + one
  `scripts/calculate.py` covering baker's percentages, yeast %, and
  poolish/biga predough math, ported from the TeigTime iOS app.
