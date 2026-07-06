#!/usr/bin/env python3
"""Predough (poolish/biga) calculator — flour/water split, predough yeast, main-dough reduction.

Ported from TeigTime's DoughCalculationService + SequentialYeastCalculationService
(Swift). Standalone: given the recipe's total flour weight and hydration (from
`calculate-bakers-percentage`), splits off the predough's share and computes
main-dough yeast either by "sequential reduction" (when the main dough's own
fermentation time/temp is known) or classic subtraction (manual main yeast %).

ponytail: duplicates the small time/temp yeast formula from the sibling
`calculate-yeast` skill rather than importing across skill directories, so
each skill stays independently installable — keep both copies in sync.
"""
import argparse
import json
import math
import sys

YEAST_CONVERSION = {"fresh": 1.0, "dry": 0.4, "instant": 0.33}
MODE_MULTIPLIER = {"neapolitan": 1.0, "roman": 1.2, "newyork": 2.5, "direct": 8.0}

TOTAL_YEAST_RANGE = {"none": (0.3, 2.0), "poolish": (0.08, 0.18), "biga": (0.1, 0.25)}
GLOBAL_TOTAL_MIN, GLOBAL_TOTAL_MAX = 0.05, 2.0
MAIN_ALONE_MAX = 0.5


def mode_multiplier(mode, custom_percent):
    if mode in MODE_MULTIPLIER:
        return MODE_MULTIPLIER[mode]
    return custom_percent / 0.5


def yeast_percent_from_time_temp(temp_c, hours, yeast_type, mode, custom_percent):
    temp_factor = 2.0 ** ((23.0 - temp_c) / 5.0)
    time_factor = math.sqrt(5.0 / hours)
    fresh_percent = 0.5 * temp_factor * time_factor * mode_multiplier(mode, custom_percent)
    return fresh_percent * YEAST_CONVERSION[yeast_type]


def classical_predough_yeast_percent(predough_type, temp_c, hours):
    """Percent of predough flour, before yeast-type conversion."""
    if hours is None:
        return {"poolish": 0.1, "biga": 0.2}[predough_type]
    if predough_type == "biga":
        if hours >= 16 and (temp_c is None or temp_c <= 20):
            return 0.15
        if hours < 12:
            return 0.2
        return 0.1
    if hours >= 10 and (temp_c is None or temp_c <= 22):  # poolish
        return 0.08
    if hours < 8:
        return 0.15
    return 0.1


def predough_efficiency(predough_type, hours):
    """Fraction by which predough reduces the main dough's own yeast need."""
    h = hours or 0.0
    if predough_type == "biga":
        if h >= 16:
            return 0.10
        if h >= 8:
            return 0.07
        return 0.03
    if h >= 12:  # poolish
        return 0.08
    if h >= 6:
        return 0.05
    if h >= 3:
        return 0.03
    return 0.01


def apply_clamps(predough_pct, main_pct, predough_type):
    """Proportionally rescale predough/main yeast percentages into realistic limits."""
    total = predough_pct + main_pct
    if total > GLOBAL_TOTAL_MAX:
        scale = GLOBAL_TOTAL_MAX / total
        predough_pct, main_pct, total = predough_pct * scale, main_pct * scale, GLOBAL_TOTAL_MAX
    elif 0 < total < GLOBAL_TOTAL_MIN:
        scale = GLOBAL_TOTAL_MIN / total
        predough_pct, main_pct, total = predough_pct * scale, main_pct * scale, GLOBAL_TOTAL_MIN

    if main_pct > MAIN_ALONE_MAX:
        main_pct = MAIN_ALONE_MAX
        total = predough_pct + main_pct

    lo, hi = TOTAL_YEAST_RANGE[predough_type]
    if total > hi:
        scale = hi / total
        predough_pct, main_pct = predough_pct * scale, main_pct * scale
    elif 0 < total < lo:
        scale = lo / total
        predough_pct, main_pct = predough_pct * scale, main_pct * scale

    return predough_pct, main_pct


def calculate(args):
    if args.flour_weight is None or args.hydration is None or args.predough_type is None:
        raise SystemExit("--flour-weight, --hydration, and --predough-type are required")
    default_hydration = 100.0 if args.predough_type == "poolish" else 55.0
    predough_hydration = args.predough_hydration if args.predough_hydration is not None else default_hydration

    predough_flour = args.flour_weight * args.predough_flour_percent / 100.0
    predough_water = predough_flour * predough_hydration / 100.0
    main_dough_flour = args.flour_weight - predough_flour
    main_dough_water = args.flour_weight * args.hydration / 100.0 - predough_water

    predough_yeast_pct_of_predough_flour = classical_predough_yeast_percent(
        args.predough_type, args.predough_temp, args.predough_hours
    )
    predough_yeast_weight = (
        predough_flour * predough_yeast_pct_of_predough_flour / 100.0 * YEAST_CONVERSION[args.yeast_type]
    )

    notes = []
    if args.main_ferment_hours is not None:
        main_temp = args.main_ferment_temp if args.main_ferment_temp is not None else 21.0
        base_percent = yeast_percent_from_time_temp(
            main_temp, args.main_ferment_hours, args.yeast_type, args.yeast_mode, args.custom_yeast_percent
        )
        efficiency = predough_efficiency(args.predough_type, args.predough_hours)
        adjusted_percent = base_percent * (1.0 - efficiency)
        main_dough_yeast_weight = args.flour_weight * adjusted_percent / 100.0
        notes.append(f"main-dough yeast reduced {efficiency:.0%} for {args.predough_type} predough")
    else:
        raw_main_percent = args.main_yeast_percent if args.main_yeast_percent is not None else args.custom_yeast_percent
        total_yeast_weight = args.flour_weight * raw_main_percent / 100.0 * YEAST_CONVERSION[args.yeast_type]
        main_dough_yeast_weight = max(0.0, total_yeast_weight - predough_yeast_weight)

    predough_pct = predough_yeast_weight / args.flour_weight * 100.0
    main_pct = main_dough_yeast_weight / args.flour_weight * 100.0
    predough_pct, main_pct = apply_clamps(predough_pct, main_pct, args.predough_type)
    predough_yeast_weight = args.flour_weight * predough_pct / 100.0
    main_dough_yeast_weight = args.flour_weight * main_pct / 100.0

    return {
        "predough_type": args.predough_type,
        "predough_flour_g": round(predough_flour, 1),
        "predough_water_g": round(predough_water, 1),
        "predough_yeast_g": round(predough_yeast_weight, 1),
        "main_dough_flour_g": round(main_dough_flour, 1),
        "main_dough_water_g": round(main_dough_water, 1),
        "main_dough_yeast_g": round(main_dough_yeast_weight, 1),
        "notes": notes,
    }


def build_arg_parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--flour-weight", type=float, help="total recipe flour weight, before split")
    p.add_argument("--hydration", type=float, help="overall recipe hydration %%")
    p.add_argument("--predough-type", choices=["poolish", "biga"])
    p.add_argument("--predough-flour-percent", type=float, default=20.0)
    p.add_argument("--predough-hydration", type=float, help="default 100 poolish / 55 biga")
    p.add_argument("--predough-hours", type=float)
    p.add_argument("--predough-temp", type=float)
    p.add_argument("--yeast-type", choices=sorted(YEAST_CONVERSION), default="fresh")
    p.add_argument("--yeast-mode", choices=list(MODE_MULTIPLIER) + ["custom"], default="neapolitan")
    p.add_argument("--custom-yeast-percent", type=float, default=0.3)
    p.add_argument("--main-ferment-hours", type=float, help="triggers sequential reduction if given")
    p.add_argument("--main-ferment-temp", type=float, help="Celsius, default 21 if --main-ferment-hours given")
    p.add_argument("--main-yeast-percent", type=float, help="manual override for the classic-subtraction path")
    p.add_argument("--json", action="store_true")
    p.add_argument("--selftest", action="store_true")
    return p


def _selfcheck():
    args = build_arg_parser().parse_args([
        "--flour-weight", "1000", "--hydration", "70", "--predough-type", "poolish",
        "--predough-flour-percent", "20",
    ])
    result = calculate(args)
    total_flour = result["predough_flour_g"] + result["main_dough_flour_g"]
    assert abs(total_flour - 1000) < 0.5, f"predough flour split mismatch: {total_flour}"
    total_water = result["predough_water_g"] + result["main_dough_water_g"]
    assert abs(total_water - 700) < 0.5, f"predough water split mismatch: {total_water}"

    predough_pct, main_pct = apply_clamps(50.0, 50.0, "none")
    lo, hi = TOTAL_YEAST_RANGE["none"]
    assert (predough_pct + main_pct) <= hi + 1e-9, "clamp failed to cap total yeast %"

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
        print(f"{result['predough_type']} predough:")
        print(f"  predough flour {result['predough_flour_g']}g  water {result['predough_water_g']}g  "
              f"yeast {result['predough_yeast_g']}g")
        print(f"  main-dough flour {result['main_dough_flour_g']}g  water {result['main_dough_water_g']}g  "
              f"yeast {result['main_dough_yeast_g']}g")
        for note in result["notes"]:
            print(f"  note: {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
