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
- **Salt level** — offer a quick pick: none / low / normal / high (or let the
  user give an exact percent or gram amount instead). Maps to:

  | Level | Salt % |
  |---|---|
  | none | 0% |
  | low | 1.2% |
  | normal | purpose default (see `calculate-bakers-percentage`'s SKILL.md) |
  | high | 3.0% |

- **Oil/fat level** — same quick-pick pattern: none / low / normal / high (or
  an exact percent/gram amount). Maps to:

  | Level | Fat % |
  |---|---|
  | none | 0% |
  | low | 1.0% |
  | normal | purpose default |
  | high | 5.0% |

- **Predough** — ask directly: none, or poolish/biga for more flavor and a
  longer ferment. If the user wants one but doesn't care which, default to
  poolish (simpler, no special flour needed).
- **Ambient/dough temperature — but only once a fermentation time is in play**
  (the user gave a fermentation duration, a ready-by time, or predough
  timing). Every 5°C roughly doubles or halves the yeast needed for the same
  time, so don't silently assume room temperature — ask, e.g. "what's the
  temperature where it'll be rising?" If the user is fine with the default
  long/forgiving ferment and gave no timing at all, skip this question —
  temperature only matters once a duration is driving the calculation.

Ask all of these together as one compact, multiple-choice-style question —
don't spread them across separate follow-up turns.

**Optional — default and state, don't block:**
- Portion size (small/normal/large, or an explicit gram weight) → defaults to normal.
- Hydration / sugar % → purpose defaults (see `calculate-bakers-percentage`'s SKILL.md).
- Yeast type (fresh/dry/instant) → defaults to fresh.
- Fermentation style (neapolitan/roman/newyork/direct) → defaults to
  neapolitan (long, forgiving), unless the user names a specific style
  explicitly (e.g. "New York style", "direct method"). Don't infer a faster
  style from urgency language alone ("ready in 4 hours" is a time, not a
  style pick) — when the user already gives an explicit fermentation time,
  that time alone should drive the calculation via `calculate-yeast`'s
  `--ferment-hours`; stacking a "direct" style multiplier on top of an
  already-short explicit time double-counts speed (verified: 4h at 21°C +
  direct mode gives 5.9% yeast, outside fresh yeast's realistic 3% ceiling —
  use neapolitan as the baseline multiplier unless the user names a style).
- Ready-by time → only used if the user gives one. Never invent a start time.

## Procedure

1. Parse the request for the mandatory fields above; ask one combined
   question if any are missing. If a fermentation time was given but no
   temperature, include the temperature question in that same combined ask
   rather than a separate follow-up.
2. Resolve every optional field to a default unless the user already gave it.
   Convert salt/oil levels to percent via the tables above.
3. **If the user gave salt or oil as an absolute gram amount** (not a percent
   or level), resolve it in two passes since grams-to-percent depends on
   flour weight, which isn't known yet: first run
   `calculate-bakers-percentage` with a placeholder (e.g. the purpose
   default) to get an approximate `flour_weight_g`, compute
   `percent = grams / flour_weight_g * 100`, then re-run with that resolved
   percent for the real numbers. Salt/fat are small percentages, so this
   converges in one extra pass — no need to iterate further.
4. Run `calculate-bakers-percentage/scripts/calculate.py` with
   `--purpose`/`--balls`/`--size or --weight`/`--hydration`/`--salt`/`--sugar`/`--fat`
   (and `--manual-yeast-percent` **only** if the user gave a fixed % and there
   is no predough and no fermentation time/temp — otherwise omit it and let
   the next steps handle yeast). Read its `flour_weight_g` from the output.
5. If a predough was requested, run
   `calculate-predough/scripts/calculate.py --flour-weight <from step 4> --hydration <recipe hydration>`
   plus the predough/main-dough fermentation flags. Its output already
   includes the correctly split flour/water/yeast for both parts — skip step 6.
6. Otherwise, if fermentation time/temp or a fixed yeast % was given, run
   `calculate-yeast/scripts/calculate.py --flour-weight <from step 4>` with
   the relevant flags to get the yeast weight.
7. If the user gave a ready-by time, sum the recipe's step durations in
   minutes and run `calculate-fermentation-schedule/scripts/calculate.py
   --total-minutes <sum> --ready-at <HH:MM>` to get a recommended start time.
8. Present a single combined ingredient list in grams, plus any notes from
   steps 5-7 (e.g. yeast reduction, recommended start time). Mention which
   defaults you assumed so the user can correct any of them.

## Example

Request: "I need a dough recipe for 4 people, normal size, ready to bake at 20:00."

- Ask (one combined question): "What are you making — pizza, bread, focaccia,
  or something else? And: salt (none/low/normal/high), oil (none/low/normal/high),
  a predough (none/poolish/biga), and what temperature it'll rise at?"
- User: "Pizza, normal salt, low oil, poolish, 20°C."
- Step 4: `calculate-bakers-percentage --purpose pizza --balls 4 --size normal --fat 1.0`
  (salt left at purpose default since "normal" was picked) → flour_weight_g ≈ 599.7
- Step 5: `calculate-predough --flour-weight 599.7 --hydration 63.5 --predough-type poolish --predough-hours 12 --main-ferment-hours 18 --main-ferment-temp 20`
  → predough + main-dough flour/water/yeast
- Step 7: sum step durations, run `calculate-fermentation-schedule --ready-at 20:00`
- Present: ingredient list + "start by ~14:00 to be ready at 20:00" + the
  poolish yeast-reduction note.
