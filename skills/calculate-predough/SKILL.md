---
name: calculate-predough
description: >
  Splits a recipe's flour/water into a poolish or biga predough plus the
  remaining main dough, and computes yeast for both (reducing the main
  dough's own yeast need when the predough already contributes rise). Use
  when the user asks for a poolish, biga, preferment, or predough, or wants
  a longer/more flavorful fermentation. Standalone, or called by the
  dough-recipe orchestrator with a flour weight from calculate-bakers-percentage.
compatibility: Requires python3 (stdlib only) on PATH.
license: MIT
---

# Calculate predough

Runs `scripts/calculate.py`, ported from TeigTime's `DoughCalculationService`
and `SequentialYeastCalculationService` (Swift).

```
predoughFlour = flourWeight × predoughFlourPercent/100     (default 20%)
predoughWater = predoughFlour × predoughHydration/100      (poolish fixed 100%, biga default 55%)
mainDoughFlour = flourWeight - predoughFlour
mainDoughWater = flourWeight × hydration/100 - predoughWater
```

**Predough yeast** (% of predough flour, before yeast-type conversion):
- No fermentation time given: poolish 0.1%, biga 0.2% (flat classical default).
- With time/temp given: biga 0.15% (≥16h & ≤20°C) / 0.2% (<12h) / else 0.1%;
  poolish 0.08% (≥10h & ≤22°C) / 0.15% (<8h) / else 0.1%.

**Main-dough yeast:**
- If the main dough's own fermentation time is known (`--main-ferment-hours`):
  "sequential reduction" — compute its base yeast % via the same time/temp
  formula as `calculate-yeast`, then reduce it by an efficiency factor (biga
  0.10 ≥16h / 0.07 ≥8h / 0.03 else; poolish 0.08 ≥12h / 0.05 ≥6h / 0.03 ≥3h /
  0.01 else) reflecting the predough's own contribution.
- Otherwise: classic subtraction — a manual total yeast % (`--main-yeast-percent`,
  default 0.3%) minus the predough's yeast share.

Both shares are then proportionally rescaled into realistic limits: total
yeast 0.05–2.0%, main-dough-alone max 0.5%, and a final clamp into the
predough type's range (biga 0.1–0.25%, poolish 0.08–0.18%, applied last).
Because those ranges are tight, predough yeast for a small batch can round to
0.0g at one decimal place — that's the clamp working as intended. If a
computed amount is under ~0.5g, it's more accurately measured as a
yeast-water slurry than on a kitchen scale.

**ponytail:** this script duplicates the small time/temp yeast formula from
the sibling `calculate-yeast` skill rather than importing across skill
directories, so each stays independently installable. Keep both in sync.

## CLI reference

```
python3 scripts/calculate.py --flour-weight GRAMS --hydration PCT --predough-type {poolish,biga} \
  [--predough-flour-percent PCT] [--predough-hydration PCT] [--predough-hours H] [--predough-temp C] \
  [--yeast-type {fresh,dry,instant}] \
  [--main-ferment-hours H] [--main-ferment-temp C] [--yeast-mode MODE] \
  [--main-yeast-percent PCT] [--json]
```

Example:

```
$ python3 scripts/calculate.py --flour-weight 599.7 --hydration 63.5 --predough-type poolish \
    --predough-hours 12 --main-ferment-hours 18 --main-ferment-temp 20
poolish predough:
  predough flour 119.9g  water 119.9g  yeast 0.0g
  main-dough flour 479.8g  water 260.9g  yeast 1.0g
  note: main-dough yeast reduced 8% for poolish predough
```
