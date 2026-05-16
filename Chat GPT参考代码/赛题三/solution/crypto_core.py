"""Core helpers for challenge problem 3.

The code follows the supplied C++ implementation for the round function.
Masks are 32-bit integers split into eight high-to-low nibbles.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, List, Sequence, Tuple


SBOX: Tuple[int, ...] = (
    0xC,
    0x6,
    0x9,
    0x0,
    0x1,
    0xA,
    0x2,
    0xB,
    0x3,
    0x8,
    0x5,
    0xD,
    0x4,
    0xE,
    0x7,
    0xF,
)


def parity(x: int) -> int:
    p = 0
    while x:
        p ^= x & 1
        x >>= 1
    return p


def nibbles(mask: int) -> Tuple[int, ...]:
    return tuple((mask >> shift) & 0xF for shift in range(28, -1, -4))


def from_nibbles(xs: Sequence[int]) -> int:
    out = 0
    for x in xs:
        out = (out << 4) | (x & 0xF)
    return out


def xor_many(xs: Iterable[int]) -> int:
    out = 0
    for x in xs:
        out ^= x
    return out & 0xF


def lat_numerators() -> List[List[int]]:
    """Return LAT[a][b] numerator in {-8,-4,0,4,8,16}.

    The correlation value is LAT[a][b] / 16 and equals C^S[b, a].
    """

    lat: List[List[int]] = [[0 for _ in range(16)] for _ in range(16)]
    for a in range(16):
        for b in range(16):
            total = 0
            for x in range(16):
                bit = parity(a & x) ^ parity(b & SBOX[x])
                total += 1 if bit == 0 else -1
            lat[a][b] = total
    return lat


LAT: List[List[int]] = lat_numerators()


def transition_weight(num: int) -> int:
    """Map LAT numerator to correlation exponent weight.

    |num|=16 -> |cor|=1 -> weight 0
    |num|=8  -> |cor|=1/2 -> weight 1
    |num|=4  -> |cor|=1/4 -> weight 2
    """

    if num == 0:
        raise ValueError("zero LAT entry has no finite weight")
    return 4 - int(round(math.log(abs(num), 2)))


def transition_sign(num: int) -> int:
    return 1 if num > 0 else -1


def transitions_by_output() -> Dict[int, List[Tuple[int, int, int]]]:
    """For each S-box output mask b, list valid input masks a.

    Each entry is (a, weight, sign), sorted by low weight first.
    """

    table: Dict[int, List[Tuple[int, int, int]]] = {}
    for b in range(16):
        vals = []
        for a in range(16):
            num = LAT[a][b]
            if num:
                vals.append((a, transition_weight(num), transition_sign(num)))
        vals.sort(key=lambda item: (item[1], item[0]))
        table[b] = vals
    return table


TRANS_BY_OUTPUT = transitions_by_output()


def transitions_by_input() -> Dict[int, List[Tuple[int, int, int]]]:
    """For each S-box input mask a, list valid output masks b.

    Each entry is (b, weight, sign), sorted by low weight first.
    """

    table: Dict[int, List[Tuple[int, int, int]]] = {}
    for a in range(16):
        vals = []
        for b in range(16):
            num = LAT[a][b]
            if num:
                vals.append((b, transition_weight(num), transition_sign(num)))
        vals.sort(key=lambda item: (item[1], item[0]))
        table[a] = vals
    return table


TRANS_BY_INPUT = transitions_by_input()


def sr_transpose(mask: int) -> int:
    """Input mask before SR from output mask after SR.

    This is A^T * mask for the SR permutation in computecor.cpp:
    y = (x0, x5, x2, x7, x4, x1, x6, x3).
    """

    g = nibbles(mask)
    beta = (g[0], g[5], g[2], g[7], g[4], g[1], g[6], g[3])
    return from_nibbles(beta)


def mc_transpose(mask: int) -> int:
    """Input mask before MC from output mask after MC.

    This follows the supplied C++ code, not the possibly OCR-damaged
    formula in the extracted PDF text.
    """

    g = nibbles(mask)
    beta = (
        g[0] ^ g[1] ^ g[3],
        g[2],
        g[0] ^ g[2] ^ g[3],
        g[0],
        g[4] ^ g[5] ^ g[7],
        g[6],
        g[4] ^ g[6] ^ g[7],
        g[4],
    )
    return from_nibbles(beta)


def round_linear_transpose(mask: int) -> int:
    """Mask before SR/MC linear layers from round output mask."""

    return sr_transpose(mc_transpose(mask))


def _matrix_rows_from_transform(transform) -> List[int]:
    rows = [0 for _ in range(8)]
    for col in range(8):
        basis = [0 for _ in range(8)]
        basis[col] = 1
        out = nibbles(transform(from_nibbles(basis)))
        for row, val in enumerate(out):
            if val & 1:
                rows[row] |= 1 << col
    return rows


def _invert_binary_matrix(rows: Sequence[int]) -> List[int]:
    aug = [(rows[i] & 0xFF) | (1 << (8 + i)) for i in range(8)]
    for col in range(8):
        pivot = None
        for row in range(col, 8):
            if (aug[row] >> col) & 1:
                pivot = row
                break
        if pivot is None:
            raise ValueError("linear layer matrix is singular")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        for row in range(8):
            if row != col and ((aug[row] >> col) & 1):
                aug[row] ^= aug[col]
    return [(aug[i] >> 8) & 0xFF for i in range(8)]


def _apply_matrix_rows(rows: Sequence[int], mask: int) -> int:
    xs = nibbles(mask)
    ys = []
    for row in rows:
        ys.append(xor_many(xs[col] for col in range(8) if (row >> col) & 1))
    return from_nibbles(ys)


ROUND_TRANSPOSE_ROWS = _matrix_rows_from_transform(round_linear_transpose)
ROUND_INV_TRANSPOSE_ROWS = _invert_binary_matrix(ROUND_TRANSPOSE_ROWS)


def round_linear_inverse_transpose(mask: int) -> int:
    """Round output mask gamma from the S-layer output mask beta.

    It returns gamma such that round_linear_transpose(gamma) == beta.
    """

    return _apply_matrix_rows(ROUND_INV_TRANSPOSE_ROWS, mask)


def contribution_value(weight: int, sign: int) -> float:
    return float(sign) * (2.0 ** (-weight))


def score(rounds: int, estimate: float) -> float:
    if estimate == 0:
        return float("-inf")
    return (2**rounds) + math.log(abs(estimate), 2)


def is_valid_estimate(true_value: float, estimate: float) -> bool:
    if estimate == 0:
        return False
    return abs(estimate - true_value) <= abs(true_value) / 4.0
