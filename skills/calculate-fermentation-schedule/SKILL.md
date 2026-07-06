---
name: calculate-fermentation-schedule
description: >
  Backward-schedules a dough's start time from a target ready-by time and
  total process duration. Use when the user gives a time they want the dough
  ready by (e.g. "ready by 8pm", "I need it tomorrow morning") and wants to
  know when to start. Never invents a start time if none is given. Standalone,
  or called by the dough-recipe orchestrator.
compatibility: Requires python3 (stdlib only) on PATH.
license: MIT
---

# Calculate fermentation schedule

Runs `scripts/calculate.py`, ported from TeigTime's
`RecipeGenerationService.recommendedStartDate` (Swift).

```
target = next occurrence of the given HH:MM at or after "now" (rolls to tomorrow if already past)
start  = target - totalProcessMinutes
```

Only call this when the user actually gave a target ready time — the app's
own rule (and this skill's) is to never invent a start time on its own; if no
`--ready-at` is given, the result is `null`/"not recommending a start time".

## CLI reference

```
python3 scripts/calculate.py --total-minutes N --ready-at HH:MM [--now-iso ISO_DATETIME] [--json]
```

`--now-iso` is only for determinism/testing — omit it to use the real current time.

Example:

```
$ python3 scripts/calculate.py --total-minutes 360 --ready-at 20:00
start by 2026-07-06T14:00:00 to be ready at 2026-07-06T20:00:00
```
