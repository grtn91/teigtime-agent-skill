# Changelog

All notable changes to this project are documented in this file. Format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
