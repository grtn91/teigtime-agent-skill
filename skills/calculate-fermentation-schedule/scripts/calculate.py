#!/usr/bin/env python3
"""Ready-by-time scheduler — backward-schedules a start time from a target ready time.

Ported from TeigTime's RecipeGenerationService.recommendedStartDate (Swift).
Only used when the user actually gives a target ready time — mirrors the
app's rule of never inventing a start time on its own.
"""
import argparse
import json
import sys
from datetime import datetime, timedelta


def recommended_start(total_minutes, ready_at, now=None):
    """ready_at: 'HH:MM' string. Returns (start_datetime, target_datetime) or (None, None)."""
    if ready_at is None:
        return None, None
    hour, _, minute = ready_at.partition(":")
    hour, minute = int(hour), int(minute)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise SystemExit(f"invalid --ready-at time: {ready_at}")

    now = now or datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)  # next occurrence of that wall-clock time

    start = target - timedelta(minutes=total_minutes)
    return start, target


def calculate(args):
    if args.total_minutes is None:
        raise SystemExit("--total-minutes is required")
    now = datetime.fromisoformat(args.now_iso) if args.now_iso else None
    start, target = recommended_start(args.total_minutes, args.ready_at, now)
    return {
        "total_minutes": args.total_minutes,
        "ready_at": args.ready_at,
        "recommended_start": start.isoformat() if start else None,
        "target_ready_at": target.isoformat() if target else None,
    }


def build_arg_parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--total-minutes", type=float, help="sum of all step durations, in minutes")
    p.add_argument("--ready-at", help="target ready time, 'HH:MM'; omit to get no recommendation")
    p.add_argument("--now-iso", help="ISO datetime to treat as 'now' (for determinism/testing)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--selftest", action="store_true")
    return p


def _selfcheck():
    now = datetime(2026, 7, 6, 14, 0)  # 14:00

    # Ready time later today (18:00) -> starts today.
    start, target = recommended_start(120, "18:00", now)
    assert target == datetime(2026, 7, 6, 18, 0), f"expected today 18:00, got {target}"
    assert start == datetime(2026, 7, 6, 16, 0), f"expected 16:00 start, got {start}"

    # Ready time already passed today (09:00) -> rolls to tomorrow.
    start, target = recommended_start(60, "09:00", now)
    assert target == datetime(2026, 7, 7, 9, 0), f"expected tomorrow 09:00, got {target}"

    # No ready time given -> never invent one.
    start, target = recommended_start(60, None, now)
    assert start is None and target is None, "should not invent a start time"

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
        if result["recommended_start"] is None:
            print("no ready-by time given — not recommending a start time")
        else:
            print(f"start by {result['recommended_start']} to be ready at {result['target_ready_at']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
