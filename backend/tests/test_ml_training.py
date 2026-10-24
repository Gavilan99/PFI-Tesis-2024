"""The training of the item cuts (app.ml.training), on synthetic data and without the database.

Covers the parts the product depends on: the bank reader, the answer -> feature contract, the
quotas and nesting of the cuts, that selection never reads the options' group_label, and a full
train run that writes artifacts the backend can load. Synthetic respondents only.
"""

import csv
import json

import joblib
import numpy as np
import pytest

from app.ml.config import TAXONOMIES
from app.ml.training import train as training
from app.ml.training.bank import LIKERT, SCENARIO, load_bank
from app.ml.training.data import load_sample
from app.ml.training.encoding import columns, encode, encode_one
from app.ml.training.selection import (check_nested, cramers_v_corrected, quotas, random_cuts,
                                       select_cuts, serve_order)
from scripts.synthetic_pilot import write_bank, write_people


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
    assert report["fold_kind"] == "stratified"
    assert "type_most_common_in_fold" in report["baseline"]
    text = json.dumps(report) + json.dumps(manifest) + (out / "evaluation.txt").read_text(encoding="utf-8")
    assert "S000" not in text                               # no respondent code leaves the script


def test_stratified_folds_keep_every_type_in_training(bank, tmp_path):
    resp, labels = write_people(tmp_path, bank)
    sample = load_sample(resp, labels, load_bank(tmp_path / "bank.csv"))
    types = np.asarray(sample.types)
    for tr, te in training.splits("stratified", 0, types):
        assert set(types[tr]) == set(types)                 # no type is left out of a training fold


def test_null_permutes_types_and_reports_p(tmp_path, bank, monkeypatch):
    monkeypatch.setattr(training, "N_TREES", 10)
    resp, labels = write_people(tmp_path, bank)
    out = tmp_path / "artifacts"
    assert training.main(["--bank", str(tmp_path / "bank.csv"), "--responses", str(resp), "--labels", str(labels),
                          "--out", str(out), "--sizes", f"12,{len(bank)}", "--reps", "1",
                          "--null-perms", "2", "--null-reps", "1"]) == 0
    report = json.loads((out / "precision_by_items.json").read_text(encoding="utf-8"))
    for cut in report["cuts"]:
        assert cut["null"]["permutations"] == 2
        assert 0 < cut["null"]["p_type"] <= 1 and 0 < cut["null"]["p_balanced"] <= 1
    sample = load_sample(resp, labels, load_bank(tmp_path / "bank.csv"))
    shuffled = training.permuted(sample, np.random.default_rng(0))
    assert sorted(shuffled.types) == sorted(sample.types) and shuffled.answers is sample.answers
