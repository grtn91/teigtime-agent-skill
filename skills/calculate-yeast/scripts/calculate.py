#!/usr/bin/env python3
"""Yeast % / weight calculator — time+temperature driven, or manual override.

Ported from TeigTime's YeastCalculationService (Swift), formula-fallback path
only (the app's on-device CoreML model is iOS-only and not portable, so it's
intentionally skipped here — this deterministic formula is the app's own
documented fallback when the model is unavailable).

Standalone: given a flour weight (from `calculate-bakers-percentage`), returns
yeast weight in grams. Also used by the sibling `calculate-predough` skill for
its main-dough sequential-reduction step (that skill duplicates the formula
below rather than importing across skill directories, so each skill stays
independently installable — keep both copies in sync if this changes).
"""
import argparse
import json
import math
import sys

YEAST_CONVERSION = {"fresh": 1.0, "dry": 0.4, "instant": 0.33}
VALID_RANGE = {"fresh": (0.01, 3.0), "dry": (0.004, 1.2), "instant": (0.003, 1.0)}

# ponytail: the app has two inconsistent mode-multiplier sets (one for its ML
# success path, a different one for its formula-fallback path). Only the
# formula path is ported here, so we use ONE consistent set — these values —
# rather than replicate the app's inconsistency.
MODE_MULTIPLIER = {"neapolitan": 1.0, "roman": 1.2, "newyork": 2.5, "direct": 8.0}


def mode_multiplier(mode, custom_percent):
    if mode in MODE_MULTIPLIER:
        return MODE_MULTIPLIER[mode]
    return custom_percent / 0.5  # custom mode


def yeast_percent_from_time_temp(temp_c, hours, yeast_type, mode, custom_percent):
    """Time/temperature -> yeast% for the given yeast type (conversion applied)."""
    temp_factor = 2.0 ** ((23.0 - temp_c) / 5.0)
    time_factor = math.sqrt(5.0 / hours)
    fresh_percent = 0.5 * temp_factor * time_factor * mode_multiplier(mode, custom_percent)
    return fresh_percent * YEAST_CONVERSION[yeast_type]


def calculate(args):
    if args.flour_weight is None:
        raise SystemExit("--flour-weight is required")
    is_manual = args.percent is not None
    if is_manual:
        yeast_percent = args.percent * YEAST_CONVERSION[args.yeast_type]
        temp_used = None
        hours_used = None
    else:
        if args.ferment_hours is None:
            raise SystemExit("either --percent or --ferment-hours is required")
        temp_used = args.ferment_temp if args.ferment_temp is not None else 21.0
        hours_used = args.ferment_hours
        yeast_percent = yeast_percent_from_time_temp(
            temp_used, hours_used, args.yeast_type, args.yeast_mode, args.custom_yeast_percent
        )

    yeast_weight = args.flour_weight * yeast_percent / 100.0
    lo, hi = VALID_RANGE[args.yeast_type]
    in_range = lo <= yeast_percent <= hi

    return {
        "is_manual": is_manual,
        "yeast_type": args.yeast_type,
        "yeast_mode": None if is_manual else args.yeast_mode,
        "ferment_temp_c": temp_used,
        "ferment_hours": hours_used,
        "yeast_percent": round(yeast_percent, 3),
        "yeast_weight_g": round(yeast_weight, 1),
        "within_typical_range": in_range,
    }


def build_arg_parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--flour-weight", type=float)
    p.add_argument("--yeast-type", choices=sorted(YEAST_CONVERSION), default="fresh")
    p.add_argument("--yeast-mode", choices=list(MODE_MULTIPLIER) + ["custom"], default="neapolitan")
    p.add_argument("--custom-yeast-percent", type=float, default=0.3)
    p.add_argument("--percent", type=float, help="manual raw yeast %% override, skips time/temp calc")
    p.add_argument("--ferment-hours", type=float)
    p.add_argument("--ferment-temp", type=float, help="Celsius, default 21 if --ferment-hours given")
    p.add_argument("--json", action="store_true")
    p.add_argument("--selftest", action="store_true")
    return p


def _selfcheck():
    # Reference point: 23C/5h/fresh/neapolitan must be ~0.5%.
    ref = yeast_percent_from_time_temp(23.0, 5.0, "fresh", "neapolitan", 0.3)
    assert abs(ref - 0.5) < 1e-9, f"reference yeast%% off: {ref}"

    args = build_arg_parser().parse_args([
        "--flour-weight", "1000", "--ferment-hours", "5", "--ferment-temp", "23",
    ])
    result = calculate(args)
    assert result["yeast_weight_g"] == 5.0, f"expected 5.0g at reference point, got {result['yeast_weight_g']}"

    # Manual override with dry yeast conversion (0.4x fresh).
    args = build_arg_parser().parse_args(["--flour-weight", "1000", "--percent", "1.0", "--yeast-type", "dry"])
    result = calculate(args)
    assert result["yeast_weight_g"] == 4.0, f"expected 4.0g dry yeast, got {result['yeast_weight_g']}"

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
        source = "manual" if result["is_manual"] else f"{result['ferment_hours']}h @ {result['ferment_temp_c']}C, {result['yeast_mode']}"
        print(f"yeast ({result['yeast_type']}, {source}): {result['yeast_percent']}% = {result['yeast_weight_g']}g")
        if not result["within_typical_range"]:
            print("  note: outside the typical range for this yeast type — double-check time/temp inputs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
