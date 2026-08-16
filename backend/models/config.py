"""Canonical Enneagram taxonomy definitions and the type -> group lookup table.

Source: standard Enneagram triad theory (Riso & Hudson / Daniels), cross-checked
during the 4-classifier architecture design (see
`01 In Progress/(C) 2026-08-11 4-classifier ML architecture design.md`).

Each of the 9 eneatypes maps to exactly one group in each of the 4 independent
taxonomies ("conjuntos de triadas"). The first 3 taxonomies alone already
uniquely determine the type -- the 4th (Relaciones Objetales) is not a logical
tie-breaker but adds robustness against classifier noise in the ML pipeline.
"""

from __future__ import annotations

# Taxonomy name -> ordered list of its 3 possible classes.
TAXONOMIES: dict[str, list[str]] = {
    "centro": ["gut", "heart", "head"],
    "horneviano": ["assertive", "compliant", "withdrawn"],
    "armonico": ["positive_outlook", "competency", "reactive"],
    "relaciones_objetales": ["attachment", "frustration", "rejection"],
}

# Eneatype (1-9) -> group label per taxonomy.
TYPE_TABLE: dict[int, dict[str, str]] = {
    1: {"centro": "gut", "horneviano": "compliant", "armonico": "competency", "relaciones_objetales": "frustration"},
    2: {"centro": "heart", "horneviano": "compliant", "armonico": "positive_outlook", "relaciones_objetales": "rejection"},
    3: {"centro": "heart", "horneviano": "assertive", "armonico": "competency", "relaciones_objetales": "attachment"},
    4: {"centro": "heart", "horneviano": "withdrawn", "armonico": "reactive", "relaciones_objetales": "frustration"},
    5: {"centro": "head", "horneviano": "withdrawn", "armonico": "competency", "relaciones_objetales": "rejection"},
    6: {"centro": "head", "horneviano": "compliant", "armonico": "reactive", "relaciones_objetales": "attachment"},
    7: {"centro": "head", "horneviano": "assertive", "armonico": "positive_outlook", "relaciones_objetales": "frustration"},
    8: {"centro": "gut", "horneviano": "assertive", "armonico": "reactive", "relaciones_objetales": "rejection"},
    9: {"centro": "gut", "horneviano": "withdrawn", "armonico": "positive_outlook", "relaciones_objetales": "attachment"},
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
