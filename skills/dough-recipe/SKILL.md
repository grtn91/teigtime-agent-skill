---
name: dough-recipe
description: >
  Computes dough recipes (pizza, bread, focaccia, bagels, ...) as exact gram
  weights by orchestrating the calculate-bakers-percentage, calculate-yeast,
  calculate-predough, and calculate-fermentation-schedule skills. Use when the
  user asks for a dough recipe, pizza dough, or bread dough, or gives a
  portion count (e.g. "4 people", "6 balls") and wants ingredient weights.
  Asks brief follow-up questions for anything required but missing, states
  sensible defaults for everything else.
metadata:
  related_skills: calculate-bakers-percentage, calculate-yeast, calculate-predough, calculate-fermentation-schedule
license: MIT
---

# Dough recipe (orchestrator)

Turns a natural-language dough request into exact gram weights by running
three or four sibling skills' scripts in sequence. This skill holds no
calculation logic of its own — it only resolves the conversation (what does
the user want, what are the defaults) and wires the sub-skills together.

Each sub-skill is also independently triggerable on its own (e.g. a lone
"what yeast % for an 18 hour ferment at 20°C?" activates just `calculate-yeast`).
This file only covers the combined "give me a full recipe" flow.

## Q&A protocol

Ask **only** for missing mandatory fields. State optional fields' defaults
inline in the same reply, and don't ask about them unless the user wants to
change one.

**Mandatory — ask if missing or ambiguous:**
- **Dough purpose** (pizza, bread, focaccia, bagel, or another type) — this
  picks the whole default table, so a bare "4 people, normal size" is missing
  exactly this and should get exactly one follow-up question.
- **Portion count** (number of balls/loaves) — only ask if truly absent (e.g.
  "make me some dough" with no quantity at all).

**Optional — default and state, don't block:**
- Portion size (small/normal/large, or an explicit gram weight) → defaults to normal.
- Hydration / salt / sugar / fat % → purpose defaults (see `calculate-bakers-percentage`'s SKILL.md).
- Yeast type (fresh/dry/instant) → defaults to fresh.
- Fermentation style (neapolitan/roman/newyork/direct) or an explicit
  time+temperature → defaults to neapolitan (long, forgiving), unless the
  user's phrasing implies same-day ("I need it tonight" → direct).
- Predough (none/poolish/biga) → defaults to none, unless the user asks for
  more flavor or a longer ferment, or the request conventionally implies one.
- Ready-by time → only used if the user gives one. Never invent a start time.

## Procedure

1. Parse the request for the mandatory fields above; ask one combined
   question if any are missing.
2. Resolve every optional field to a default unless the user already gave it.
3. Run `calculate-bakers-percentage/scripts/calculate.py` with
   `--purpose`/`--balls`/`--size or --weight`/`--hydration`/`--salt`/`--sugar`/`--fat`
   (and `--manual-yeast-percent` **only** if the user gave a fixed % and there
   is no predough and no fermentation time/temp — otherwise omit it and let
   step 4/5 handle yeast). Read its `flour_weight_g` from the output.
4. If a predough was requested, run
   `calculate-predough/scripts/calculate.py --flour-weight <from step 3> --hydration <recipe hydration>`
   plus the predough/main-dough fermentation flags. Its output already
   includes the correctly split flour/water/yeast for both parts — skip step 5.
5. Otherwise, if fermentation time/temp or a fixed yeast % was given, run
   `calculate-yeast/scripts/calculate.py --flour-weight <from step 3>` with
   the relevant flags to get the yeast weight.
6. If the user gave a ready-by time, sum the recipe's step durations in
   minutes and run `calculate-fermentation-schedule/scripts/calculate.py
   --total-minutes <sum> --ready-at <HH:MM>` to get a recommended start time.
7. Present a single combined ingredient list in grams, plus any notes from
   steps 4-6 (e.g. yeast reduction, recommended start time). Mention which
   defaults you assumed so the user can correct any of them.

## Example

Request: "I need a dough recipe for 4 people, normal size, with a poolish,
ready to bake at 20:00."

- Ask: "What are you making — pizza, bread, focaccia, or something else?"
- User: "Pizza."
- Step 3: `calculate-bakers-percentage --purpose pizza --balls 4 --size normal`
  → flour_weight_g ≈ 599.7
- Step 4: `calculate-predough --flour-weight 599.7 --hydration 63.5 --predough-type poolish --predough-hours 12 --main-ferment-hours 18 --main-ferment-temp 20`
  → predough + main-dough flour/water/yeast
- Step 6: sum step durations, run `calculate-fermentation-schedule --ready-at 20:00`
- Present: ingredient list + "start by ~14:00 to be ready at 20:00" + the
  poolish yeast-reduction note.
