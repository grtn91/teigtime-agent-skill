---
name: calculate-yeast
description: >
  Computes yeast percentage and weight from fermentation time and
  temperature (or a manual override), for fresh, dry, or instant yeast. Use
  when the user asks how much yeast to use for a given fermentation time/
  temperature, wants to convert between yeast types, or mentions "yeast
  percentage", "fermentation schedule", or a specific rise time and
  temperature. Standalone, or called by the dough-recipe orchestrator with a
  flour weight from calculate-bakers-percentage.
compatibility: Requires python3 (stdlib only) on PATH.
license: MIT
---

# Calculate yeast

Runs `scripts/calculate.py`, which implements the time/temperature → yeast %
formula ported from TeigTime's `YeastCalculationService` (Swift) — the app's
own deterministic formula-fallback path (its on-device CoreML model is
iOS-only and intentionally not ported here).

```
tempFactor = 2 ^ ((23 - tempC) / 5)     # every 5°C colder doubles yeast need
timeFactor = sqrt(5 / hours)            # reference: 23°C, 5h, 0.5% fresh yeast
freshYeastPercent = 0.5 × tempFactor × timeFactor × modeMultiplier
yeastPercent = freshYeastPercent × conversionRatio
yeastWeight = flourWeight × yeastPercent/100
```

| Yeast type | Conversion ratio | Typical %% range |
|---|---|---|
| fresh | 1.0 | 0.01–3.0% |
| dry | 0.4 | 0.004–1.2% |
| instant | 0.33 | 0.003–1.0% |

| Fermentation style | Mode multiplier |
|---|---|
| neapolitan (long, forgiving) | 1.0 |
| roman | 1.2 |
| newyork | 2.5 |
| direct (same-day) | 8.0 |
| custom | `customPercent / 0.5` |

Pass `--percent` instead of `--ferment-hours`/`--ferment-temp` for a manual
override (skips the formula, applies only the yeast-type conversion).

## CLI reference

```
python3 scripts/calculate.py --flour-weight GRAMS \
  [--yeast-type {fresh,dry,instant}] [--yeast-mode {neapolitan,roman,newyork,direct,custom}] \
  [--ferment-hours H] [--ferment-temp C] [--percent PCT] [--json]
```

Example:

```
$ python3 scripts/calculate.py --flour-weight 600 --ferment-hours 18 --ferment-temp 20 --yeast-mode neapolitan
yeast (fresh, 18.0h @ 20.0C, neapolitan): 0.4% = 2.4g
```
