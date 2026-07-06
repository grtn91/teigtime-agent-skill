---
name: calculate-bakers-percentage
description: >
  Converts dough baker's percentages (hydration, salt, sugar, fat) and a
  portion count/size into exact flour/water/salt/sugar/fat gram weights. Use
  when the user asks to scale a dough recipe, convert baker's percentages to
  grams, or gives a dough weight/ball count with hydration and wants the
  ingredient weights. Standalone, or called by the dough-recipe orchestrator.
compatibility: Requires python3 (stdlib only) on PATH.
license: MIT
---

# Calculate baker's percentage

Runs `scripts/calculate.py`, which implements the core baker's-percentage
formula ported from TeigTime's `DoughCalculationService` (Swift):

```
totalDoughWeight = ballCount × ballWeight
totalPercentage  = 100 (flour) + hydration% + salt% + sugar% + fat% + (manual yeast% if given)
flourWeight = totalDoughWeight / (totalPercentage / 100)
water/salt/sugar/fat = flourWeight × their %/100
```

This skill does **not** compute yeast weight from fermentation time/temperature
or predough splits — see the sibling `calculate-yeast` and `calculate-predough`
skills for those. Only pass `--manual-yeast-percent` here if the whole recipe
uses a single fixed yeast % with no predough and no auto-calculation; otherwise
leave it out and let the other skills add yeast on top of this skill's
`flour_weight_g`.

## Default table (by purpose)

Mirrors TeigTime's own AI-recipe-generation prompt (pizza/bread rows) plus new,
reasonable defaults for focaccia/bagel:

| Purpose | Normal weight | Hydration | Salt | Sugar | Fat |
|---|---|---|---|---|---|
| Pizza | 250 g/ball | 63.5% | 2.25% | 0% | ~1% |
| Bread | 750 g/loaf | 71.5% | 2.0% | 0% | 0% |
| Focaccia | 500 g/pan | 72.5% | 2.0% | 0% | ~3% |
| Bagel | 100 g/each | 56.5% | 2.0% | ~1% | 0% |
| Generic | 250 g | 65% | 2.0% | 0% | 0% |

Small/normal/large sizing: small ≈ −20% of normal, large ≈ +20%, rounded
(e.g. pizza 200/250/300g). Pass `--weight` to override with an explicit gram
value instead.

If the user describes salt or oil/fat as a level rather than a percent, map
it to `--salt`/`--fat` like this (independent of purpose, except "normal"
which still means the purpose default above):

| Level | Salt % | Fat % |
|---|---|---|
| none | 0% | 0% |
| low | 1.2% | 1.0% |
| normal | purpose default | purpose default |
| high | 3.0% | 5.0% |

If the user gives an absolute gram amount instead of a percent/level, this
script only accepts percent — convert first: run once with a placeholder to
get an approximate `flour_weight_g`, compute `percent = grams / flour_weight_g * 100`,
then re-run with that percent for the final numbers (salt/fat are small
percentages, so one extra pass is enough to converge).

## CLI reference

```
python3 scripts/calculate.py --purpose {pizza,bread,focaccia,bagel,generic} --balls N \
  [--size {small,normal,large} | --weight GRAMS] \
  [--hydration PCT] [--salt PCT] [--sugar PCT] [--fat PCT] \
  [--manual-yeast-percent PCT] [--yeast-type {fresh,dry,instant}] [--json]
```

Example:

```
$ python3 scripts/calculate.py --purpose pizza --balls 4 --size normal --json
{
  "purpose": "pizza", "ball_count": 4, "ball_weight_g": 250, "total_dough_weight_g": 1000,
  "flour_weight_g": 599.7, "water_weight_g": 380.8, "salt_weight_g": 13.5, "fat_weight_g": 6.0, ...
}
```
