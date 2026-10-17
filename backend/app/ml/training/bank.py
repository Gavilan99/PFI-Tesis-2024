"""The question bank as the training sees it: one `Item` per question, in bank order.

Read from the bank CSV (`research/bank/NureonAI Prototype v4.1.2.csv`): one row per option, with the
item code (`question_id`, e.g. `Q001`), its grouping system in Spanish and its format. The Spanish
system labels are translated to the canonical vocabulary with the same table the importer uses.
Option `group_label`s are read only to count options: they never enter features or selection.
"""

from __future__ import annotations

import csv
import unicodedata
from dataclasses import dataclass
from pathlib import Path

SCENARIO = "scenario"
LIKERT = "likert"

# Same translation as scripts/import_question_bank.py (GROUPING_SYSTEMS).
SYSTEM_BY_BANK_LABEL = {
    "Centros de Inteligencia": "intelligence_centers",
    "Conjunto Horneviano": "hornevian",
    "Conjunto Armónico": "harmonic",
    "Conjunto de Relaciones Objetales": "object_relations",
}


@dataclass(frozen=True)
class Item:
    code: str            # bank code, e.g. "Q001"
    order: int           # position in the bank, 1-based (Q001 -> 1)
    system: str          # canonical grouping system the item was written for (authoring tag)
    fmt: str             # SCENARIO or LIKERT
    n_options: int       # 3 for scenarios, 5 for Likert


def _key(label: str) -> str:
    return unicodedata.normalize("NFC", label).strip().casefold()


_SYSTEMS = {_key(k): v for k, v in SYSTEM_BY_BANK_LABEL.items()}


def load_bank(path: str | Path) -> list[Item]:
    rows: dict[str, list[dict]] = {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            rows.setdefault(row["question_id"].strip(), []).append(row)
    items = []
    for code, opts in rows.items():
        system = _SYSTEMS.get(_key(opts[0]["grouping_system"]))
        if system is None:
            raise ValueError(f"{code}: unknown grouping system {opts[0]['grouping_system']!r}")
        fmt = opts[0]["format"].strip()
        if fmt not in (SCENARIO, LIKERT):
            raise ValueError(f"{code}: unknown format {fmt!r}")
        expected = 3 if fmt == SCENARIO else 5
        if len(opts) != expected:
            raise ValueError(f"{code}: {len(opts)} options, expected {expected}")
        items.append(Item(code=code, order=int(code.lstrip("Qq")), system=system, fmt=fmt, n_options=expected))
    items.sort(key=lambda it: it.order)
    return items
