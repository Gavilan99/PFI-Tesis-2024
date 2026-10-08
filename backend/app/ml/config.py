"""Canonical Enneagram taxonomy definitions and the type -> group lookup table.

Source: standard Enneagram triad theory (Riso & Hudson / Daniels), cross-checked
during the 4-classifier architecture design (see
`01 In Progress/(C) 2026-08-11 4-classifier ML architecture design.md`).

Each of the 9 eneatypes maps to exactly one group in each of the 4 independent
taxonomies ("conjuntos de triadas"). The first 3 taxonomies alone already
uniquely determine the type -- the 4th (object_relations) is not a logical
tie-breaker but adds robustness against classifier noise in the ML pipeline.
"""

from __future__ import annotations

from app.db.models.enums import GROUPS_BY_SYSTEM

# Taxonomy name -> ordered list of its 3 possible classes. Derived from the canonical vocabulary
# (`grouping_system` -> `group_label`, see CLAUDE.md), so there is one vocabulary, not two copies.
TAXONOMIES: dict[str, list[str]] = {system.value: list(groups) for system, groups in GROUPS_BY_SYSTEM.items()}

# Eneatype (1-9) -> group label per taxonomy.
TYPE_TABLE: dict[int, dict[str, str]] = {
    1: {"intelligence_centers": "gut", "hornevian": "compliant", "harmonic": "competency", "object_relations": "frustration"},
    2: {"intelligence_centers": "heart", "hornevian": "compliant", "harmonic": "positive_outlook", "object_relations": "rejection"},
    3: {"intelligence_centers": "heart", "hornevian": "assertive", "harmonic": "competency", "object_relations": "attachment"},
    4: {"intelligence_centers": "heart", "hornevian": "withdrawn", "harmonic": "reactive", "object_relations": "frustration"},
    5: {"intelligence_centers": "head", "hornevian": "withdrawn", "harmonic": "competency", "object_relations": "rejection"},
    6: {"intelligence_centers": "head", "hornevian": "compliant", "harmonic": "reactive", "object_relations": "attachment"},
    7: {"intelligence_centers": "head", "hornevian": "assertive", "harmonic": "positive_outlook", "object_relations": "frustration"},
    8: {"intelligence_centers": "gut", "hornevian": "assertive", "harmonic": "reactive", "object_relations": "rejection"},
    9: {"intelligence_centers": "gut", "hornevian": "withdrawn", "harmonic": "positive_outlook", "object_relations": "attachment"},
}


def validate_type_table() -> None:
    """Sanity check: every type must have a valid class for every taxonomy,
    and no two types may share the same tuple across all 4 taxonomies."""
    seen_tuples = set()
    for eneatype, groups in TYPE_TABLE.items():
        assert set(groups.keys()) == set(TAXONOMIES.keys()), f"type {eneatype} missing a taxonomy"
        for taxonomy, group in groups.items():
            assert group in TAXONOMIES[taxonomy], f"type {eneatype}: '{group}' not valid for '{taxonomy}'"
        tup = tuple(groups[t] for t in TAXONOMIES)
        assert tup not in seen_tuples, f"type {eneatype} duplicates another type's full tuple"
        seen_tuples.add(tup)


if __name__ == "__main__":
    validate_type_table()
    print(f"OK: {len(TYPE_TABLE)} types, {len(TAXONOMIES)} taxonomies, all tuples unique.")
