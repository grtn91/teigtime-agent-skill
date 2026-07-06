# Changelog

All notable changes to this project are documented in this file. Format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
