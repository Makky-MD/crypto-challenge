#!/usr/bin/env python3
"""Beam search for high-correlation linear trails.

This searches backward from output mask v to input masks u.  It is a fast
engineering baseline and a candidate generator for later SAT/MILP models.
"""

from __future__ import annotations

import argparse
import heapq
from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Iterable, List, Sequence, Tuple

from crypto_core import (
    TRANS_BY_OUTPUT,
    contribution_value,
    from_nibbles,
    nibbles,
    round_linear_transpose,
    score,
)


@dataclass(frozen=True)
class Trail:
    mask: int
    weight: int
    sign: int
    path: Tuple[int, ...]

    @property
    def contribution(self) -> float:
        return contribution_value(self.weight, self.sign)


def combo_stream(beta_nibbles: Sequence[int]) -> Iterable[Tuple[int, int, int]]:
    """Yield S-box predecessor combinations by nondecreasing weight.

    Each yielded item is (alpha_mask, added_weight, added_sign).
    """

    lists = [TRANS_BY_OUTPUT[b] for b in beta_nibbles]
    start = tuple(0 for _ in lists)
    start_weight = sum(lists[i][0][1] for i in range(8))
    start_sign = 1
    start_alpha = []
    for i in range(8):
        a, _, s = lists[i][0]
        start_alpha.append(a)
        start_sign *= s

    heap: List[Tuple[int, Tuple[int, ...], Tuple[int, ...], int]] = [
        (start_weight, start, tuple(start_alpha), start_sign)
    ]
    seen = {start}

    while heap:
        weight, idxs, alpha, sign = heapq.heappop(heap)
        yield from_nibbles(alpha), weight, sign

        for pos in range(8):
            nxt = list(idxs)
            nxt[pos] += 1
            if nxt[pos] >= len(lists[pos]):
                continue
            nxt_t = tuple(nxt)
            if nxt_t in seen:
                continue
            seen.add(nxt_t)

            old_i = idxs[pos]
            new_i = nxt[pos]
            old_a, old_w, old_s = lists[pos][old_i]
            new_a, new_w, new_s = lists[pos][new_i]
            new_alpha = list(alpha)
            new_alpha[pos] = new_a
            new_weight = weight - old_w + new_w
            new_sign = sign * old_s * new_s
            heapq.heappush(
                heap,
                (new_weight, nxt_t, tuple(new_alpha), new_sign),
            )


def expand_trail(trail: Trail, limit: int) -> List[Trail]:
    beta = round_linear_transpose(trail.mask)
    out: List[Trail] = []
    for i, (alpha, added_w, added_s) in enumerate(combo_stream(nibbles(beta))):
        if i >= limit:
            break
        out.append(
            Trail(
                mask=alpha,
                weight=trail.weight + added_w,
                sign=trail.sign * added_s,
                path=(alpha,) + trail.path,
            )
        )
    return out


def prune(trails: Iterable[Trail], beam: int, per_mask: int) -> List[Trail]:
    buckets: DefaultDict[int, List[Trail]] = defaultdict(list)
    for tr in trails:
        buckets[tr.mask].append(tr)

    kept: List[Trail] = []
    for vals in buckets.values():
        vals.sort(key=lambda tr: (tr.weight, -tr.sign, tr.path))
        kept.extend(vals[:per_mask])

    kept.sort(key=lambda tr: (tr.weight, -tr.sign, tr.mask, tr.path))
    return kept[:beam]


def search(rounds: int, v: int, beam: int, expand: int, per_mask: int) -> List[Trail]:
    current = [Trail(mask=v, weight=0, sign=1, path=(v,))]
    for _ in range(rounds):
        expanded: List[Trail] = []
        for tr in current:
            expanded.extend(expand_trail(tr, expand))
        current = prune(expanded, beam=beam, per_mask=per_mask)
    return current


def grouped_estimates(trails: Sequence[Trail], top: int) -> List[Tuple[int, float, int, int]]:
    grouped: DefaultDict[int, List[Trail]] = defaultdict(list)
    for tr in trails:
        if tr.mask != 0:
            grouped[tr.mask].append(tr)

    rows = []
    for u, vals in grouped.items():
        estimate = sum(tr.contribution for tr in vals)
        if estimate == 0:
            continue
        best_weight = min(tr.weight for tr in vals)
        rows.append((u, estimate, len(vals), best_weight))
    rows.sort(key=lambda row: (-score_cached_abs(row[1]), row[3], row[0]))
    return rows[:top]


def score_cached_abs(estimate: float) -> float:
    return abs(estimate)


def parse_hex(x: str) -> int:
    return int(x, 16 if x.lower().startswith("0x") else 10)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", "-r", type=int, required=True)
    parser.add_argument("--v", type=parse_hex, required=True, help="output mask")
    parser.add_argument("--u", type=parse_hex, help="optional input mask filter")
    parser.add_argument("--beam", type=int, default=20000)
    parser.add_argument("--expand", type=int, default=128)
    parser.add_argument("--per-mask", type=int, default=8)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--show-path", action="store_true")
    args = parser.parse_args()

    trails = search(
        rounds=args.rounds,
        v=args.v,
        beam=args.beam,
        expand=args.expand,
        per_mask=args.per_mask,
    )

    if args.u is not None:
        selected = [tr for tr in trails if tr.mask == args.u]
        estimate = sum(tr.contribution for tr in selected)
        print(
            "r=%d u=0x%08x v=0x%08x routes=%d VE=%.17g score=%.8f"
            % (args.rounds, args.u, args.v, len(selected), estimate, score(args.rounds, estimate))
        )
        for tr in sorted(selected, key=lambda item: (item.weight, item.path))[: args.top]:
            print(
                "  w=%d sign=%+d cor=%.17g path=%s"
                % (
                    tr.weight,
                    tr.sign,
                    tr.contribution,
                    " -> ".join("0x%08x" % x for x in tr.path),
                )
            )
        return 0

    print(
        "# r=%d v=0x%08x beam=%d expand=%d per_mask=%d kept_routes=%d"
        % (args.rounds, args.v, args.beam, args.expand, args.per_mask, len(trails))
    )
    for u, estimate, count, best_weight in grouped_estimates(trails, args.top):
        print(
            "u=0x%08x v=0x%08x routes=%d best_w=%d VE=%.17g score=%.8f"
            % (u, args.v, count, best_weight, estimate, score(args.rounds, estimate))
        )
        if args.show_path:
            shown = 0
            for tr in sorted((tr for tr in trails if tr.mask == u), key=lambda x: (x.weight, x.path)):
                print(
                    "  w=%d sign=%+d cor=%.17g path=%s"
                    % (
                        tr.weight,
                        tr.sign,
                        tr.contribution,
                        " -> ".join("0x%08x" % x for x in tr.path),
                    )
                )
                shown += 1
                if shown >= 3:
                    break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

