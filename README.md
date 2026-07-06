# teigtime-agent-skill

A set of Claude [Agent Skills](https://agentskills.io/specification) that
compute dough recipes (pizza, bread, focaccia, bagels...) from a
natural-language request, using the same baker's-percentage / yeast% /
poolish-biga-predough math as the [TeigTime](https://apps.apple.com/app/teigtime)
iOS app.

## Structure

One orchestrator skill plus four standalone calculation skills, each
independently triggerable:

- `skills/dough-recipe` — orchestrator: runs the Q&A, then chains the skills below.
- `skills/calculate-bakers-percentage` — flour/water/salt/sugar/fat from dough weight + %.
- `skills/calculate-yeast` — time/temperature (or manual) → yeast % and weight.
- `skills/calculate-predough` — poolish/biga flour/water split + yeast, with main-dough reduction.
- `skills/calculate-fermentation-schedule` — backward-schedules a start time from a ready-by time.

Each skill has its own `SKILL.md` and a self-contained `scripts/calculate.py`
(stdlib-only Python, run `--selftest` on any of them to verify the math).

## Install

```
/plugin marketplace add grtn91/teigtime-agent-skill
/plugin install dough-recipe
```

Or, for local development, from a clone of this repo:

```
/plugin marketplace add .
/plugin install dough-recipe
```

## Example

> **You:** I need a dough recipe for 4 people, normal size.
>
> **Claude:** What are you making — pizza, bread, focaccia, or something
> else? I'll use 63.5% hydration, 2.25% salt, fresh yeast, no predough unless
> you want one.
>
> **You:** Pizza.
>
> **Claude:** *(runs `calculate-bakers-percentage/scripts/calculate.py --purpose pizza --balls 4 --size normal`)*
> 4 × 250g pizza dough balls (1000g total):
> flour 599.7g, water 380.8g, yeast (fresh) 1.8g, salt 13.5g, oil 6g.

See [`skills/dough-recipe/SKILL.md`](skills/dough-recipe/SKILL.md) for the
orchestrator, or any sub-skill's `SKILL.md` for its formulas.

## License

MIT
