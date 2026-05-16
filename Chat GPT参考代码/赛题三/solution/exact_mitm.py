#!/usr/bin/env python3
"""Meet-in-the-middle exact linear-hull sum for fixed (r,u,v)."""

from __future__ import annotations

import argparse
from collections import defaultdict
from typing import DefaultDict, Iterable, List, Sequence, Tuple

from beam_topk import combo_stream, parse_hex
from crypto_core import (
    TRANS_BY_INPUT,
    contribution_value,
    from_nibbles,
    nibbles,
    round_linear_inverse_transpose,
    round_linear_transpose,
    score,
)


def forward_combo_stream(alpha_nibbles: Sequence[int]):
    lists = [TRANS_BY_INPUT[a] for a in alpha_nibbles]

    def rec(pos: int, beta: List[int], weight: int, sign: int):
        if pos == 8:
            yield from_nibbles(beta), weight, sign
            return
        for b, w, s in lists[pos]:
            beta.append(b)
            yield from rec(pos + 1, beta, weight + w, sign * s)
            beta.pop()

    yield from rec(0, [], 0, 1)


def expand_backward(current: DefaultDict[int, float], max_states: int) -> DefaultDict[int, float]:
    nxt: DefaultDict[int, float] = defaultdict(float)
    for gamma, coeff in current.items():
        beta = round_linear_transpose(gamma)
        for alpha, added_w, added_s in combo_stream(nibbles(beta)):
            nxt[alpha] += coeff * contribution_value(added_w, added_s)
            if len(nxt) > max_states:
                raise RuntimeError("backward state limit exceeded: %d > %d" % (len(nxt), max_states))
    return nxt


def expand_forward(current: DefaultDict[int, float], max_states: int) -> DefaultDict[int, float]:
    nxt: DefaultDict[int, float] = defaultdict(float)
    for alpha, coeff in current.items():
        for beta, added_w, added_s in forward_combo_stream(nibbles(alpha)):
            gamma = round_linear_inverse_transpose(beta)
            nxt[gamma] += coeff * contribution_value(added_w, added_s)
            if len(nxt) > max_states:
                raise RuntimeError("forward state limit exceeded: %d > %d" % (len(nxt), max_states))
    return nxt


def exact_mitm(rounds: int, u: int, v: int, split: int, max_states: int, verbose: bool = True) -> float:
    if split < 0 or split > rounds:
        raise ValueError("split must be in [0, rounds]")

    fwd: DefaultDict[int, float] = defaultdict(float)
    fwd[u] = 1.0
    for i in range(split):
        fwd = expand_forward(fwd, max_states)
        if verbose:
            print("# forward_round=%d states=%d" % (i + 1, len(fwd)))

    bwd: DefaultDict[int, float] = defaultdict(float)
    bwd[v] = 1.0
    for i in range(rounds - split):
        bwd = expand_backward(bwd, max_states)
        if verbose:
            print("# backward_round=%d states=%d" % (i + 1, len(bwd)))

    if len(fwd) > len(bwd):
        fwd, bwd = bwd, fwd
    return sum(coeff * bwd.get(mask, 0.0) for mask, coeff in fwd.items())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", "-r", type=int, required=True)
    parser.add_argument("--u", type=parse_hex, required=True)
    parser.add_argument("--v", type=parse_hex, required=True)
    parser.add_argument("--split", type=int, default=1)
    parser.add_argument("--max-states", type=int, default=2000000)
    args = parser.parse_args()

    val = exact_mitm(args.rounds, args.u, args.v, args.split, args.max_states)
    print(
        "r=%d u=0x%08x v=0x%08x exact_mitm=%.17g score=%.8f"
        % (args.rounds, args.u, args.v, val, score(args.rounds, val))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
