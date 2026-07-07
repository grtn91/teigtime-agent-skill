#!/usr/bin/env python3
"""Prints the real current system time (ISO8601). No branching logic — just a
forced OS time lookup, so a schedule is never built on the model's guess of
'now' instead of the actual clock.
"""
import sys
from datetime import datetime


def main(argv=None):
    print(datetime.now().isoformat())
    return 0


if __name__ == "__main__":
    sys.exit(main())
