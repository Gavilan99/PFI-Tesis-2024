"""The answer -> feature contract shared by training and inference.

For each item of a cut, in the cut's column order:
- a scenario item becomes three 0/1 columns `Qxxx_o1`, `Qxxx_o2`, `Qxxx_o3` (one-hot of the chosen
  option position);
- a Likert item becomes one integer column `Qxxx` with the chosen position, 1 to 5 (1 = "Muy en
  desacuerdo", 5 = "Muy de acuerdo").

The position is the option's place in the bank's order, 1-based: `Answer.option_position`. A cut's
model only ever sees the items of its cut, all answered, so there is no "not asked" value.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from app.ml.training.bank import SCENARIO, Item


def columns(items: Sequence[Item]) -> list[str]:
    out: list[str] = []
    for it in items:
        if it.fmt == SCENARIO:
            out += [f"{it.code}_o{k}" for k in range(1, it.n_options + 1)]
        else:
            out.append(it.code)
    return out


def encode_one(positions: Mapping[str, int], items: Sequence[Item]) -> list[int]:
    """One person's answers ({item code: chosen position}) -> one feature row. Every item of the
    cut must be answered with a valid position; anything else is an error, never a default."""
    row: list[int] = []
    for it in items:
        if it.code not in positions:
            raise ValueError(f"{it.code} is part of the cut and has no answer")
        p = int(positions[it.code])
        if not 1 <= p <= it.n_options:
            raise ValueError(f"{it.code}: position {p} outside 1..{it.n_options}")
        if it.fmt == SCENARIO:
            row += [int(p == k) for k in range(1, it.n_options + 1)]
        else:
            row.append(p)
    return row


def encode(people: Sequence[Mapping[str, int]], items: Sequence[Item]) -> np.ndarray:
    return np.array([encode_one(p, items) for p in people], dtype=np.int64).reshape(len(people), -1)
