#!/usr/bin/env python3
"""Call the supplied exact C++ program and check an estimate."""

from __future__ import annotations

import argparse
import math
import os
import re
import subprocess
from pathlib import Path

from crypto_core import is_valid_estimate, score


ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / "computecor"


def build() -> None:
    subprocess.run(["make"], cwd=str(ROOT), check=True)


def compute_true(rounds: int, u: int, v: int, timeout: int) -> float:
    if not EXE.exists():
        build()
    payload = "%d\n0x%08x\n0x%08x\n" % (rounds, u, v)
    proc = subprocess.run(
        [str(EXE)],
        cwd=str(ROOT),
        input=payload,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=True,
    )
    match = re.search(r"Correlation\s*=\s*([-+0-9.eE]+)", proc.stdout)
    if not match:
        raise RuntimeError("could not parse exact correlation:\n" + proc.stdout + proc.stderr)
    return float(match.group(1))


def parse_int(x: str) -> int:
    return int(x, 16 if x.lower().startswith("0x") else 10)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", "-r", type=int, required=True)
    parser.add_argument("--u", type=parse_int, required=True)
    parser.add_argument("--v", type=parse_int, required=True)
    parser.add_argument("--estimate", type=float, required=True)
    parser.add_argument("--timeout", type=int, default=3600)
    args = parser.parse_args()

    true_value = compute_true(args.rounds, args.u, args.v, args.timeout)
    ok = is_valid_estimate(true_value, args.estimate)
    print("@(%d, 0x%08x, 0x%08x, %.17g, %.17g)" % (args.rounds, args.u, args.v, true_value, args.estimate))
    print("valid=%s score=%.8f abs_error=%.17g" % (ok, score(args.rounds, args.estimate), abs(args.estimate - true_value)))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

