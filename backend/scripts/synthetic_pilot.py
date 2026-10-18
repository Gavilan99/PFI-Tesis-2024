"""Synthetic pilot data for development and tests: a small bank and respondents, never real people.

Moved unchanged from tests/test_ml_training.py, so the training tests and
scripts/make_dev_artifacts.py generate the same respondents. Not part of the production image.
"""

import csv
from pathlib import Path

import numpy as np

from app.ml.config import TAXONOMIES, TYPE_TABLE
from app.ml.training.bank import SCENARIO

SYSTEMS_ES = ["Centros de Inteligencia", "Conjunto Horneviano", "Conjunto Armónico",
              "Conjunto de Relaciones Objetales"]
GROUPS_ES = {"Centros de Inteligencia": ["Cuerpo", "Corazón", "Mente"],
             "Conjunto Horneviano": ["Asertiva", "Complaciente", "Retraída"],
             "Conjunto Armónico": ["Positiva", "Competente", "Reactiva"],
             "Conjunto de Relaciones Objetales": ["Apego", "Frustración", "Rechazo"]}
CANON = dict(zip(SYSTEMS_ES, TAXONOMIES))


def write_bank(path: Path, per_system=(6, 3)) -> list[str]:
    """A small bank with the real CSV layout: per system, scenarios then Likert items."""
    rows, codes, n = [], [], 0
    for system in SYSTEMS_ES:
        for fmt, count in zip(("scenario", "likert"), per_system):
            for _ in range(count):
                n += 1
                code = f"Q{n:03d}"; codes.append(code)
                opts = GROUPS_ES[system] if fmt == "scenario" else [GROUPS_ES[system][0]] * 5
                for k, g in enumerate(opts, 1):
                    rows.append({"question_id": code, "grouping_system": system,
                                 "question_type": "scenario" if fmt == "scenario" else "multiple_choice",
                                 "format": fmt, "prompt": f"ítem {code}", "option_text": f"opción {k}",
                                 "group_label": g, "type_coverage": "", "polarity": "", "display_order": k,
                                 "origin": "N"})
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return codes


def write_people(tmp: Path, items, n=45, seed=0):
    """Synthetic respondents whose answers to the first item of each system follow their group."""
    rng = np.random.default_rng(seed)
    types = [t for t in range(1, 10) for _ in range(n // 9)]
    resp, labels = [], []
    informative = {}
    for it in items:
        informative.setdefault((it.system, it.fmt), it.code)
    for i, t in enumerate(types):
        code = f"S{i:03d}"
        row = {"respondent_id": code}
        for it in items:
            pos = int(rng.integers(1, it.n_options + 1))
            if informative.get((it.system, it.fmt)) == it.code:
                g = TYPE_TABLE[t][it.system]
                idx = TAXONOMIES[it.system].index(g)
                pos = idx + 1 if it.fmt == SCENARIO else (5 if idx == 0 else 1)
            row[it.code] = pos
        resp.append(row); labels.append({"codigo": code, "tipo_asignado": t})
    for name, rows in (("responses.csv", resp), ("labels.csv", labels)):
        with open(tmp / name, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return tmp / "responses.csv", tmp / "labels.csv"
