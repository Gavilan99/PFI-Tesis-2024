"""Probability-weighted intersection / tie-break layer.

Combines the 4 taxonomy classifiers' probability outputs into a single
eneatype prediction (1-9), per the design in
`01 In Progress/(C) 2026-08-11 4-classifier ML architecture design.md`.

Score(type) = sum over the 4 taxonomies of P(classifier predicts that type's
group in that taxonomy). Argmax over the 9 types wins. This subsumes the
"first 3 agree, 4th breaks ties" rule from the thesis's manual methodology,
but degrades gracefully under real classifier uncertainty instead of needing
hardcoded if/else branches.
"""

from __future__ import annotations

from models.config import TYPE_TABLE


def score_types(proba_by_taxonomy: dict[str, dict[str, float]]) -> dict[int, float]:
    """proba_by_taxonomy: {taxonomy_name: {class_label: probability}} for ONE sample.

    Returns: {eneatype: score}, score in [0, 4].
    """
    scores: dict[int, float] = {}
    for eneatype, groups in TYPE_TABLE.items():
        score = 0.0
        for taxonomy, group_label in groups.items():
            score += proba_by_taxonomy[taxonomy].get(group_label, 0.0)
        scores[eneatype] = score
    return scores


def predict_eneatype(proba_by_taxonomy: dict[str, dict[str, float]]) -> tuple[int, float, float]:
    """Returns (predicted_eneatype, top_score, margin_over_runner_up).

    `margin` is a rough confidence signal: a thin margin between the top-2
    candidate types means the result is ambiguous and could be surfaced to
    the user as "leaning type X, close to type Y" instead of a flat answer.
    """
    scores = score_types(proba_by_taxonomy)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_type, top_score = ranked[0]
    runner_up_score = ranked[1][1] if len(ranked) > 1 else 0.0
    return top_type, top_score, top_score - runner_up_score


def predict_eneatypes_batch(proba_lists_by_taxonomy: dict[str, list[dict[str, float]]]) -> list[tuple[int, float, float]]:
    """Batch version. proba_lists_by_taxonomy[taxonomy] is a list of per-sample proba dicts,
    all lists must be the same length and aligned by index (same sample order)."""
    n = len(next(iter(proba_lists_by_taxonomy.values())))
    results = []
    for i in range(n):
        sample_proba = {taxonomy: proba_lists_by_taxonomy[taxonomy][i] for taxonomy in proba_lists_by_taxonomy}
        results.append(predict_eneatype(sample_proba))
    return results
