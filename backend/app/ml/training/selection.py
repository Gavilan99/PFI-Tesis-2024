"""Which items go into each cut: selection by discrimination, under balance constraints.

Score of an item: the bias-corrected Cramér's V (Bergsma, 2013) between the chosen position and the
respondent's group, computed in each of the four systems and averaged. It measures how much the
answers people gave relate to who they are. The options' `group_label` is never read.

Balance: every cut keeps the bank's share of items per (grouping system, format) stratum, by largest
remainder. Within each stratum the highest-scoring items are taken. Quotas grow with the cut size,
so the cuts are nested: the items of a smaller cut are always inside the next one.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from app.ml.training.bank import LIKERT, SCENARIO, Item

SYSTEM_ORDER = ("intelligence_centers", "hornevian", "harmonic", "object_relations")
FORMAT_ORDER = (SCENARIO, LIKERT)


def _codes(values: Sequence) -> np.ndarray:
    _, inv = np.unique(np.asarray(values), return_inverse=True)
    return inv


def cramers_v_corrected(x: Sequence, y: Sequence) -> float:
    xi, yi = _codes(x), _codes(y)
    r, k = xi.max() + 1, yi.max() + 1
    table = np.bincount(xi * k + yi, minlength=r * k).reshape(r, k).astype(float)
    table = table[table.sum(1) > 0][:, table.sum(0) > 0]
    r, k = table.shape
    n = table.sum()
    if r < 2 or k < 2 or n < 3:
        return 0.0
    expected = table.sum(1, keepdims=True) * table.sum(0, keepdims=True) / n
    chi2 = ((table - expected) ** 2 / expected).sum()
    phi2 = max(0.0, chi2 / n - (k - 1) * (r - 1) / (n - 1))
    rc, kc = r - (r - 1) ** 2 / (n - 1), k - (k - 1) ** 2 / (n - 1)
    return float(np.sqrt(phi2 / max(1e-12, min(kc - 1, rc - 1))))


def item_scores(answers: Sequence[dict[str, int]], groups: dict[str, Sequence[str]],
                items: Sequence[Item], rows: Sequence[int] | None = None) -> dict[str, float]:
    """Mean corrected V over the four systems, using only `rows` (the training fold)."""
    rows = list(range(len(answers))) if rows is None else list(rows)
    out = {}
    for it in items:
        x = [answers[i][it.code] for i in rows]
        out[it.code] = float(np.mean([cramers_v_corrected(x, [groups[s][i] for i in rows]) for s in SYSTEM_ORDER]))
    return out


def strata(items: Sequence[Item]) -> dict[tuple[str, str], list[Item]]:
    out = {(s, f): [] for s in SYSTEM_ORDER for f in FORMAT_ORDER}
    for it in items:
        out[(it.system, it.fmt)].append(it)
    return {k: v for k, v in out.items() if v}


def quotas(items: Sequence[Item], size: int) -> dict[tuple[str, str], int]:
    """Largest-remainder allocation of `size` items over the strata, proportional to the bank.
    Ties in the remainder go to the stratum listed first (system order, then scenario before Likert)."""
    st = strata(items)
    total = sum(len(v) for v in st.values())
    if not 0 < size <= total:
        raise ValueError(f"cut size {size} outside 1..{total}")
    exact = {k: size * len(v) / total for k, v in st.items()}
    q = {k: int(np.floor(e)) for k, e in exact.items()}
    order = sorted(st, key=lambda k: (-(exact[k] - q[k]), list(st).index(k)))
    for k in order[: size - sum(q.values())]:
        q[k] += 1
    return q


def check_nested(items: Sequence[Item], sizes: Sequence[int]) -> None:
    prev = None
    for size in sorted(sizes):
        q = quotas(items, size)
        if prev and any(q[k] < prev[k] for k in q):
            raise ValueError(f"quotas for {size} are not a superset of the previous cut")
        prev = q


def select_cuts(scores: dict[str, float], items: Sequence[Item], sizes: Sequence[int]) -> list[list[Item]]:
    """Nested cuts by score. Ties in score go to the earlier item in the bank."""
    check_nested(items, sizes)
    ranked = {k: sorted(v, key=lambda it: (-scores[it.code], it.order)) for k, v in strata(items).items()}
    return [[it for k, v in ranked.items() for it in v[: quotas(items, size)[k]]] for size in sorted(sizes)]


def random_cuts(items: Sequence[Item], sizes: Sequence[int], rng: np.random.Generator) -> list[list[Item]]:
    """Control: nested cuts with the same quotas, items drawn at random within each stratum."""
    check_nested(items, sizes)
    shuffled = {k: [v[i] for i in rng.permutation(len(v))] for k, v in strata(items).items()}
    return [[it for k, v in shuffled.items() for it in v[: quotas(items, size)[k]]] for size in sorted(sizes)]


def serve_order(cut: Sequence[Item], previous: Sequence[Item], scores: dict[str, float]) -> list[Item]:
    """The items a cut adds over the previous one, in the order to show them: round-robin across the
    four systems (so no system comes in a block), best score first within each system."""
    seen = {it.code for it in previous}
    new = [it for it in cut if it.code not in seen]
    per_system = {s: sorted([it for it in new if it.system == s], key=lambda it: (-scores[it.code], it.order))
                  for s in SYSTEM_ORDER}
    out = []
    while any(per_system.values()):
        for s in SYSTEM_ORDER:
            if per_system[s]:
                out.append(per_system[s].pop(0))
    return out


def spearman(a: Sequence[float], b: Sequence[float]) -> float:
    def ranks(v):
        v = np.asarray(v, dtype=float)
        order = np.argsort(v, kind="mergesort")
        r = np.empty(len(v)); r[order] = np.arange(len(v), dtype=float)
        for val in np.unique(v):           # average ranks for ties
            m = v == val
            r[m] = r[m].mean()
        return r
    ra, rb = ranks(a), ranks(b)
    if ra.std() == 0 or rb.std() == 0:
        return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])
