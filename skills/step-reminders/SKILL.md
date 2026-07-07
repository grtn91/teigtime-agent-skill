---
name: step-reminders
description: >
  Builds a step-by-step clock-time timeline for a dough process (mix, bulk
  ferment, shape, final proof, bake, ...) from an ordered list of step
  durations, and optionally sets up real reminders for when each step is
  done. Use when the user asks when their fermentation will be done, wants a
  process timeline/schedule, or wants to be reminded/pinged at each step.
  Standalone, or called by the dough-recipe orchestrator once a recipe is computed.
compatibility: >
  Requires python3 (stdlib only) for the timeline itself. Active reminders
  additionally require a host agent that supports the /schedule skill
  (CronCreate) for one-time scheduled runs — falls back to showing the
  static timeline only if that isn't available.
license: MIT
---

# Step reminders

Runs `scripts/timeline.py` to turn an ordered list of named steps + durations
into absolute clock times, using `scripts/now.py` (or an already-known start
time) as the real starting point — never the model's own guess of "now".
This is the forward-scheduling counterpart to the sibling
`calculate-fermentation-schedule` skill, which only backward-schedules a
single start time from a target ready-by time.

## Typical non-fermentation step durations

The dough-calculation skills only output ingredient weights, not a step
list — build one from whatever fermentation/predough durations are already
known (main ferment, predough ferment) plus these reasonable defaults for
the quick steps:

| Step | Typical duration |
|---|---|
| Mix | 15 min |
| Divide/shape | 15–20 min (more balls → more time) |
| Bake | 15–25 min, depending on purpose (pizza ~15 min, bread ~25 min) |

## Two-tier behavior

1. **Always**: compute and show the static timeline via `timeline.py`. This
   works everywhere, no host dependency.
2. **Only if the user says yes to reminders**: for each step with duration
   ≥ 15 minutes (skip near-instant steps like mixing — nothing to remind
   about there), use the `schedule` skill (the `Skill` tool with
   `skill: "schedule"`, or the `CronCreate` tool directly if already loaded)
   to create a one-time scheduled run at that step's absolute end time, with
   a prompt telling the user what just finished and what's next.

   Creating a scheduled run is a real, visible, lasting action — confirm
   with the user before creating each one (or the whole batch at once),
   don't treat "yes, remind me" as blanket permission to silently schedule
   several cloud-agent runs.

   If `/schedule`/`CronCreate` isn't available in the current host, say so
   plainly and offer only the static timeline — don't fail silently.

## CLI reference

```
python3 scripts/now.py
# 2026-07-07T09:44:48.574253

python3 scripts/timeline.py [--start-iso ISO_DATETIME] --step "Name:Minutes" [--step ...] [--json]
```

Example:

```
$ python3 scripts/timeline.py --start-iso 2026-07-07T18:00:00 \
    --step "Mix:15" --step "Bulk ferment:240" --step "Shape:20" --step "Bake:20"
  18:00-18:15  Mix (15 min)
  18:15-22:15  Bulk ferment (240 min)
  22:15-22:35  Shape (20 min)
  22:35-22:55  Bake (20 min)
Done at 22:55
```

Omit `--start-iso` to start from the real current time (via the same logic
as `now.py`) instead of an explicit one.
