#!/usr/bin/env python3
"""Generate conservative valid candidate lines using Beam + MITM checking."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Iterable, List, Tuple

from beam_topk import grouped_estimates, parse_hex, search
from crypto_core import is_valid_estimate, score
from exact_mitm import exact_mitm


def parse_vs(raw: str) -> List[int]:
    return [parse_hex(part.strip()) for part in raw.split(",") if part.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", "-r", type=int, default=3)
    parser.add_argument("--vs", default="0x0000000f,0x000f0000")
    parser.add_argument("--beam", type=int, default=50000)
    parser.add_argument("--expand", type=int, default=128)
    parser.add_argument("--per-mask", type=int, default=4)
    parser.add_argument("--top-per-v", type=int, default=4)
    parser.add_argument("--split", type=int, default=1)
    parser.add_argument("--max-states", type=int, default=1000000)
    parser.add_argument(
        "--output",
        default="代码学/赛题三/solution/candidates.txt",
        help="output txt path relative to repository root or absolute",
    )
    args = parser.parse_args()

    lines: List[str] = []
    total = 0.0
    for v in parse_vs(args.vs):
        trails = search(args.rounds, v, args.beam, args.expand, args.per_mask)
        rows = grouped_estimates(trails, args.top_per_v)
        for u, estimate, route_count, best_weight in rows:
            true_value = exact_mitm(
                args.rounds,
                u,
                v,
                args.split,
                args.max_states,
                verbose=False,
            )
            ok = is_valid_estimate(true_value, estimate)
            line = "@(%d, 0x%08x, 0x%08x, %.17g, %.17g)" % (
                args.rounds,
                u,
                v,
                true_value,
                estimate,
            )
            rel = abs(estimate - true_value) / abs(true_value) if true_value else float("inf")
            print(
                "%s routes=%d best_w=%d rel_err=%.6g score=%.8f %s"
                % (line, route_count, best_weight, rel, score(args.rounds, estimate), "OK" if ok else "DROP")
            )
            if ok:
                lines.append(line)
                total += score(args.rounds, estimate)

    output = Path(args.output)
    if not output.is_absolute():
        output = Path.cwd() / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    print("# wrote %d valid candidates to %s" % (len(lines), output))
    print("# total_score=%.8f" % total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

