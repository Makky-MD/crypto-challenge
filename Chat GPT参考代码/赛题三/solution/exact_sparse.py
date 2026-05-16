#!/usr/bin/env python3
"""Exact sparse linear-hull propagation for low-activity masks.

This is not meant to replace the supplied exhaustive C++ checker for final
independent verification.  It is a fast sanity checker for sparse masks:
starting from v, expand all nonzero trails backward for a small number of
rounds and aggregate exact dyadic float contributions by input mask u.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from typing import DefaultDict, Iterable, Sequence, Tuple

from beam_topk import combo_stream, parse_hex
from crypto_core import contribution_value, nibbles, round_linear_transpose, score


def propagate(rounds: int, v: int, max_states: int) -> DefaultDict[int, float]:
    current: DefaultDict[int, float] = defaultdict(float)
    current[v] = 1.0
    for rd in range(rounds):
        nxt: DefaultDict[int, float] = defaultdict(float)
        expanded = 0
        for gamma, coeff in current.items():
            beta = round_linear_transpose(gamma)
            for alpha, added_w, added_s in combo_stream(nibbles(beta)):
                nxt[alpha] += coeff * contribution_value(added_w, added_s)
                expanded += 1
                if len(nxt) > max_states:
                    raise RuntimeError(
                        "state limit exceeded after round %d: %d > %d"
                        % (rd + 1, len(nxt), max_states)
                    )
        print(
            "# after_round=%d input_states=%d output_states=%d expanded_edges=%d"
            % (rd + 1, len(current), len(nxt), expanded)
        )
        current = nxt
    return current


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", "-r", type=int, required=True)
    parser.add_argument("--v", type=parse_hex, required=True)
    parser.add_argument("--u", type=parse_hex)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--max-states", type=int, default=2000000)
    args = parser.parse_args()

    values = propagate(args.rounds, args.v, args.max_states)
    if args.u is not None:
        ve = values.get(args.u, 0.0)
        print(
            "r=%d u=0x%08x v=0x%08x exact_sparse=%.17g score=%.8f"
            % (args.rounds, args.u, args.v, ve, score(args.rounds, ve))
        )
        return 0

    rows = [(u, val) for u, val in values.items() if u != 0 and val != 0]
    rows.sort(key=lambda row: (-abs(row[1]), row[0]))
    for u, val in rows[: args.top]:
        print(
            "u=0x%08x v=0x%08x exact_sparse=%.17g score=%.8f"
            % (u, args.v, val, score(args.rounds, val))
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

