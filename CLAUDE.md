# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

A Claude Agent Skills marketplace plugin (per the [agentskills.io
spec](https://agentskills.io/specification)) that computes dough recipes —
baker's percentages, yeast %, poolish/biga predough — from natural-language
requests. The math is ported from the [TeigTime](https://apps.apple.com/app/teigtime)
iOS app's Swift services, not reimplemented from scratch; when in doubt about
a formula, TeigTime's `DoughCalculationService`/`YeastCalculationService`/
`SequentialYeastCalculationService`/`PredoughType` are the ground truth.

## Architecture

One orchestrator skill, four standalone calculation skills, all under `skills/`:

- `skills/dough-recipe` — orchestrator. Holds the Q&A protocol (mandatory vs.
  optional fields) and the procedure for chaining the other four skills. No
  calculation logic of its own.
- `skills/calculate-bakers-percentage` — flour/water/salt/sugar/fat from a
  dough purpose + portion count/size.
- `skills/calculate-yeast` — time/temperature (or manual override) → yeast %
  and weight.
- `skills/calculate-predough` — poolish/biga flour/water split, predough
  yeast, and main-dough yeast reduction.
- `skills/calculate-fermentation-schedule` — backward-schedules a start time
  from a ready-by time; never invents one if not given.

Each skill is a standalone directory (`SKILL.md` + `scripts/calculate.py`)
that must remain independently installable — this is why
`calculate-predough` **duplicates** the small time/temp yeast formula from
`calculate-yeast` rather than importing across skill directories (marked with
a `ponytail:` comment in both scripts). If you change that formula, change it
in both places.

## Conventions

- Scripts are stdlib-only Python (`argparse`/`math`/`json`/`datetime`), no
  dependencies. `compatibility: Requires python3` in each SKILL.md's
  frontmatter is the one real environment requirement.
- Every script has a `--selftest` flag that runs an assert-based check (no
  test framework) — run it after touching any formula:
  ```
  for s in skills/*/scripts/calculate.py; do python3 "$s" --selftest; done
  ```
- `name:` in each `SKILL.md`'s frontmatter must match its parent directory
  exactly (spec requirement).
- The `skills` array lives in `.claude-plugin/marketplace.json`'s plugin
  entry, not in `plugin.json` — confirmed against two real reference repos
  (`academic-research-skills`, `claude-plugin-product-management`); don't
  move it back.
- Deliberate deviations from the app (documented inline where they occur,
  don't "fix" them back to match the app): the on-device CoreML yeast model
  is skipped (iOS-only, not portable) in favor of the app's own documented
  formula-fallback path; the formula's fermentation-mode multipliers use one
  consistent set rather than the app's two inconsistent ones; small/normal/large
  portion sizing is a new addition, not app-derived.

## Verification

```
for s in skills/*/scripts/calculate.py; do python3 "$s" --selftest; done
```

For an end-to-end sanity check, chain a couple of scripts manually and
compare against hand-computed baker's percentages (see any `SKILL.md`'s
"Example" section for a worked case).
