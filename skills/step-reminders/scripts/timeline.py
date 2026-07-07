#!/usr/bin/env python3
"""Forward step timeline — an ordered step list + a start time -> absolute
clock start/end time for each step.

Forward-scheduling counterpart to calculate-fermentation-schedule's backward
scheduling (which only computes a single start time from a target ready time).
Never assumes "now" from the model — defaults to the real system clock, or
takes an explicit --start-iso (e.g. a start time already computed elsewhere).
"""
import argparse
import json
import sys
from datetime import datetime, timedelta


def parse_step(raw):
    name, _, minutes = raw.rpartition(":")
    if not name:
        raise SystemExit(f"invalid --step (expected 'Name:Minutes'): {raw}")
    try:
        minutes = float(minutes)
    except ValueError:
        raise SystemExit(f"invalid --step duration (expected a number): {raw}")
    return name, minutes


def build_timeline(start, steps):
    """steps: list of (name, minutes). Returns list of dicts with start/end."""
    timeline = []
    cursor = start
    for name, minutes in steps:
        end = cursor + timedelta(minutes=minutes)
        timeline.append({
            "name": name,
            "duration_minutes": minutes,
            "start": cursor.isoformat(),
            "end": end.isoformat(),
        })
        cursor = end
    return timeline


def calculate(args):
    if not args.step:
        raise SystemExit("at least one --step is required")
    start = datetime.fromisoformat(args.start_iso) if args.start_iso else datetime.now()
    steps = [parse_step(s) for s in args.step]
    timeline = build_timeline(start, steps)
    return {
        "start": start.isoformat(),
        "finish": timeline[-1]["end"] if timeline else start.isoformat(),
        "steps": timeline,
    }


def build_arg_parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start-iso", help="ISO datetime to start from; default is the real current time")
    p.add_argument("--step", action="append", help="'Name:Minutes', repeatable, in order")
    p.add_argument("--json", action="store_true")
    p.add_argument("--selftest", action="store_true")
    return p


def _selfcheck():
    start = datetime(2026, 7, 7, 18, 0)
    timeline = build_timeline(start, [("Mix", 15), ("Bulk ferment", 240), ("Shape", 20), ("Bake", 20)])

    assert timeline[0]["start"] == "2026-07-07T18:00:00", timeline[0]["start"]
    assert timeline[0]["end"] == "2026-07-07T18:15:00", timeline[0]["end"]
    assert timeline[1]["start"] == "2026-07-07T18:15:00", timeline[1]["start"]
    assert timeline[1]["end"] == "2026-07-07T22:15:00", timeline[1]["end"]
    assert timeline[-1]["end"] == "2026-07-07T22:55:00", timeline[-1]["end"]

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
        for step in result["steps"]:
            start_hm = step["start"][11:16]
            end_hm = step["end"][11:16]
            print(f"  {start_hm}-{end_hm}  {step['name']} ({step['duration_minutes']:g} min)")
        print(f"Done at {result['finish'][11:16]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
