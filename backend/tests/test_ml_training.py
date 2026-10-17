"""The training of the item cuts (app.ml.training), on synthetic data and without the database.

Covers the parts the product depends on: the bank reader, the answer -> feature contract, the
quotas and nesting of the cuts, that selection never reads the options' group_label, and a full
train run that writes artifacts the backend can load. Synthetic respondents only.
"""

import csv
import json
from pathlib import Path

import joblib
import numpy as np
import pytest

from app.ml.config import TAXONOMIES, TYPE_TABLE
from app.ml.training import train as training
from app.ml.training.bank import LIKERT, SCENARIO, load_bank
from app.ml.training.data import load_sample
from app.ml.training.encoding import columns, encode, encode_one
from app.ml.training.selection import (check_nested, cramers_v_corrected, quotas, random_cuts,
                                       select_cuts, serve_order)

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


@pytest.fixture
def bank(tmp_path):
    write_bank(tmp_path / "bank.csv")
    return load_bank(tmp_path / "bank.csv")


def test_bank_reader_translates_systems_and_orders_items(bank):
    assert [it.order for it in bank] == list(range(1, len(bank) + 1))
    assert {it.system for it in bank} == set(TAXONOMIES)
    assert {it.n_options for it in bank if it.fmt == SCENARIO} == {3}
    assert {it.n_options for it in bank if it.fmt == LIKERT} == {5}


def test_encoding_contract(bank):
    sc = next(it for it in bank if it.fmt == SCENARIO)
    lk = next(it for it in bank if it.fmt == LIKERT)
    assert columns([sc, lk]) == [f"{sc.code}_o1", f"{sc.code}_o2", f"{sc.code}_o3", lk.code]
    assert encode_one({sc.code: 2, lk.code: 5}, [sc, lk]) == [0, 1, 0, 5]
    with pytest.raises(ValueError):
        encode_one({sc.code: 2}, [sc, lk])                 # unanswered item of the cut
    with pytest.raises(ValueError):
        encode_one({sc.code: 4, lk.code: 1}, [sc, lk])     # position out of range
    assert encode([{sc.code: 1, lk.code: 3}], [sc, lk]).shape == (1, 4)


def test_quotas_are_proportional_and_nested(bank):
    sizes = (12, 24, len(bank))
    check_nested(bank, sizes)
    for size in sizes:
        assert sum(quotas(bank, size).values()) == size
    q = quotas(bank, 12)
    assert all(q[(s, SCENARIO)] == 2 and q[(s, LIKERT)] == 1 for s in TAXONOMIES)


def test_cuts_are_nested_and_balanced(bank):
    scores = {it.code: float(it.order % 7) for it in bank}
    cuts = select_cuts(scores, bank, (12, 24, len(bank)))
    for small, big in zip(cuts, cuts[1:]):
        assert {it.code for it in small} <= {it.code for it in big}
    rnd = random_cuts(bank, (12, 24, len(bank)), np.random.default_rng(1))
    assert [len(c) for c in rnd] == [12, 24, len(bank)]
    order = serve_order(cuts[1], cuts[0], scores)
    assert {it.code for it in order} == {it.code for it in cuts[1]} - {it.code for it in cuts[0]}
    assert [it.system for it in order[:4]] == list(TAXONOMIES)          # round-robin, no blocks


def test_selection_never_reads_group_label(tmp_path, bank):
    resp, labels = write_people(tmp_path, bank)
    s1 = load_sample(resp, labels, bank)
    scrambled = tmp_path / "bank_scrambled.csv"
    rows = list(csv.DictReader(open(tmp_path / "bank.csv", encoding="utf-8")))
    for r in rows:
        r["group_label"] = "Mente"                          # labels say nothing anymore
    with open(scrambled, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    from app.ml.training.selection import item_scores
    a = item_scores(s1.answers, s1.groups, bank)
    b = item_scores(s1.answers, s1.groups, load_bank(scrambled))
    assert a == b


def test_cramers_v_detects_association_and_not_noise():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 3, 300)
    assert cramers_v_corrected(y, y) > 0.9
    assert cramers_v_corrected(rng.integers(0, 3, 300), y) < 0.1


def test_full_run_writes_loadable_artifacts(tmp_path, bank, monkeypatch):
    monkeypatch.setattr(training, "N_TREES", 20)
    resp, labels = write_people(tmp_path, bank)
    out = tmp_path / "artifacts"
    assert training.main(["--bank", str(tmp_path / "bank.csv"), "--responses", str(resp), "--labels", str(labels),
                          "--out", str(out), "--sizes", f"12,24,{len(bank)}", "--reps", "1"]) == 0
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((out / "precision_by_items.json").read_text(encoding="utf-8"))
    assert [c["size"] for c in manifest["cuts"]] == [12, 24, len(bank)]
    assert len(manifest["model_version"]) <= 64
    for cut in manifest["cuts"]:
        for system in TAXONOMIES:
            model = joblib.load(out / cut["directory"] / f"{system}.joblib")
            assert list(model.named_steps) == ["rf"]
            assert set(model.classes_) <= set(TAXONOMIES[system])
            assert model.n_features_in_ == len(cut["columns"])
    assert all("estimated_type_accuracy" in c for c in report["cuts"])
    text = json.dumps(report) + json.dumps(manifest) + (out / "evaluation.txt").read_text(encoding="utf-8")
    assert "S000" not in text                               # no respondent code leaves the script
