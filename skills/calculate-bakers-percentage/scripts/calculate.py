#!/usr/bin/env python3
"""Baker's-percentage core calculator — flour/water/salt/sugar/fat from dough weight and %.

Ported from TeigTime's DoughCalculationService (Swift). Standalone: takes a
dough purpose + portion count/size and resolves default hydration/salt/sugar/fat
unless overridden. Does not handle yeast timing or predough — see the sibling
`calculate-yeast` and `calculate-predough` skills for those; the orchestrating
`dough-recipe` skill wires them together via this script's `flour_weight_g` output.
"""
import argparse
import json
import sys

YEAST_CONVERSION = {"fresh": 1.0, "dry": 0.4, "instant": 0.33}

PURPOSE_TABLE = {
    "pizza": {"normal_weight": 250, "hydration": 63.5, "salt": 2.25, "sugar": 0.0, "fat": 1.0},
    "bread": {"normal_weight": 750, "hydration": 71.5, "salt": 2.0, "sugar": 0.0, "fat": 0.0},
    "focaccia": {"normal_weight": 500, "hydration": 72.5, "salt": 2.0, "sugar": 0.0, "fat": 3.0},
    "bagel": {"normal_weight": 100, "hydration": 56.5, "salt": 2.0, "sugar": 1.0, "fat": 0.0},
    "generic": {"normal_weight": 250, "hydration": 65.0, "salt": 2.0, "sugar": 0.0, "fat": 0.0},
}

# small/normal/large: new design (not app-derived beyond the "normal" row) —
# normal = PURPOSE_TABLE row, small ~= -20%, large ~= +20%, rounded.
SIZE_MULTIPLIER = {"small": 0.8, "normal": 1.0, "large": 1.2}


def resolve_weight(purpose, size, explicit_weight):
    if explicit_weight is not None:
        return explicit_weight
    return round(PURPOSE_TABLE[purpose]["normal_weight"] * SIZE_MULTIPLIER[size])


def calculate(args):
    purpose = PURPOSE_TABLE[args.purpose]
    weight = resolve_weight(args.purpose, args.size, args.weight)
    hydration = args.hydration if args.hydration is not None else purpose["hydration"]
    salt = args.salt if args.salt is not None else purpose["salt"]
    sugar = args.sugar if args.sugar is not None else purpose["sugar"]
    fat = args.fat if args.fat is not None else purpose["fat"]

    total_dough_weight = args.balls * weight
    manual_yeast_percent = args.manual_yeast_percent or 0.0
    total_percentage = 100.0 + hydration + salt + sugar + fat + manual_yeast_percent
    flour_weight = total_dough_weight / (total_percentage / 100.0)
    water_weight = flour_weight * hydration / 100.0
    salt_weight = flour_weight * salt / 100.0 if salt > 0 else 0.0
    sugar_weight = flour_weight * sugar / 100.0 if sugar > 0 else 0.0
    fat_weight = flour_weight * fat / 100.0 if fat > 0 else 0.0

    manual_yeast_weight = None
    if args.manual_yeast_percent is not None:
        manual_yeast_weight = flour_weight * args.manual_yeast_percent / 100.0 * YEAST_CONVERSION[args.yeast_type]

    return {
        "purpose": args.purpose,
        "ball_count": args.balls,
        "ball_weight_g": weight,
        "total_dough_weight_g": round(total_dough_weight),
        "hydration_percent": hydration,
        "salt_percent": salt,
        "sugar_percent": sugar,
        "fat_percent": fat,
        "flour_weight_g": round(flour_weight, 1),
        "water_weight_g": round(water_weight, 1),
        "salt_weight_g": round(salt_weight, 1) if salt_weight else 0.0,
        "sugar_weight_g": round(sugar_weight, 1) if sugar_weight else 0.0,
        "fat_weight_g": round(fat_weight, 1) if fat_weight else 0.0,
        "manual_yeast_weight_g": round(manual_yeast_weight, 1) if manual_yeast_weight is not None else None,
    }


def build_arg_parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--purpose", choices=sorted(PURPOSE_TABLE), default="generic")
    p.add_argument("--balls", type=int, default=1)
    p.add_argument("--size", choices=sorted(SIZE_MULTIPLIER), default="normal")
    p.add_argument("--weight", type=float, help="explicit grams per ball/loaf, overrides --size")
    p.add_argument("--hydration", type=float, help="percent, overrides purpose default")
    p.add_argument("--salt", type=float, help="percent, overrides purpose default")
    p.add_argument("--sugar", type=float, help="percent, overrides purpose default")
    p.add_argument("--fat", type=float, help="percent, overrides purpose default")
    p.add_argument("--manual-yeast-percent", type=float,
                   help="if the recipe has no auto-calculated/predough yeast, pass its raw %% here so it's "
                        "correctly included in the baker's-percentage total; omit when calculate-yeast or "
                        "calculate-predough will handle yeast separately")
    p.add_argument("--yeast-type", choices=sorted(YEAST_CONVERSION), default="fresh")
    p.add_argument("--json", action="store_true")
    p.add_argument("--selftest", action="store_true")
    return p


def _selfcheck():
    # 1 ball @ 162g, hydration 60%, salt 2%, no yeast/sugar/fat -> totalPercentage 162
    # -> flourWeight = 162/1.62 = 100g exactly.
    args = build_arg_parser().parse_args([
        "--purpose", "generic", "--balls", "1", "--weight", "162",
        "--hydration", "60", "--salt", "2", "--sugar", "0", "--fat", "0",
    ])
    result = calculate(args)
    assert result["flour_weight_g"] == 100, f"flour weight off: {result['flour_weight_g']}"
    assert result["water_weight_g"] == 60, f"water weight off: {result['water_weight_g']}"
    assert result["salt_weight_g"] == 2, f"salt weight off: {result['salt_weight_g']}"
    assert result["manual_yeast_weight_g"] is None, "manual yeast should be absent when not requested"

    # size mapping
    args = build_arg_parser().parse_args(["--purpose", "pizza", "--balls", "1", "--size", "large"])
    assert resolve_weight("pizza", "large", None) == 300
    print("OK")


def main(argv=None):
    args = build_arg_parser().parse_args(argv)
    if args.selftest:
        _selfcheck()
        return 0
    result = calculate(args)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{result['purpose']} — {result['ball_count']} x {result['ball_weight_g']}g "
              f"({result['total_dough_weight_g']}g total, {result['hydration_percent']}% hydration)")
        print(f"  flour {result['flour_weight_g']}g  water {result['water_weight_g']}g", end="")
        if result["salt_weight_g"]:
            print(f"  salt {result['salt_weight_g']}g", end="")
        if result["sugar_weight_g"]:
            print(f"  sugar {result['sugar_weight_g']}g", end="")
        if result["fat_weight_g"]:
            print(f"  fat {result['fat_weight_g']}g", end="")
        if result["manual_yeast_weight_g"] is not None:
            print(f"  yeast {result['manual_yeast_weight_g']}g", end="")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
