"""Train the product's classifiers on the pilot and estimate the accuracy of each cut.

    python -m app.ml.training.train \
        --bank ../research/bank/"NureonAI Prototype v4.1.2.csv" \
        --responses %NUREON_DATA%/responses_wide.csv \
        --labels %NUREON_DATA%/tipificaciones_piloto.csv \
        --out app/ml/artifacts

Two stages (pilot analysis plan, section 6 nonies; PDR "Product Classifier and Fixed Item Cuts"):

1. Evaluation. 5-fold cross-validation repeated 20 times, one row per respondent, so every split is
   by person. The folds are stratified by type (section 6 terdecies): with types of two or three people,
   plain folds leave a type concentrated in the test fold and missing from training, which biases every
   estimate down; predicting the most common type scores 15 % instead of 20 % with plain folds. In each fold, items are scored and the cuts selected using the training fold only, the
   four Random Forests of each cut are trained on it, and the held-out fold is predicted. The same
   folds also train random balanced cuts of the same sizes: the control that shows whether selecting
   by discrimination earns anything. The full-bank cut has no selection and reproduces the
   registered protocol (section 6 ter). Split-half stability of the item ranking is reported too.
   Optionally (`--null-perms`), the same evaluation with the type permuted across respondents: the
   accuracy the procedure reaches with no signal at all, against which each cut is read.
2. Final models. Items scored on every respondent, the cuts selected, and one set of four Random
   Forests trained per cut on all respondents.

Writes to --out (default for the product: `app/ml/artifacts/`, outside the repository): `cut_040/`,
`cut_090/`, `cut_145/` with one `<system>.joblib` per system (a scikit-learn `Pipeline` whose only
step, `rf`, is the forest), plus `manifest.json` (items and columns of each cut, serving order,
versions) and `precision_by_items.json` (the estimated accuracy the product shows after each cut,
with the control and the stability).
Only aggregates are written or printed: no respondent code ever leaves this script.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.pipeline import Pipeline

from app.ml.config import TAXONOMIES, TYPE_TABLE
from app.ml.intersection import predict_eneatype
from app.ml.training.bank import load_bank
from app.ml.training.data import Sample, load_sample, read_list
from app.ml.training.encoding import columns, encode
from app.ml.training.selection import (SYSTEM_ORDER, item_scores, random_cuts, select_cuts,
                                       serve_order, spearman)

N_TREES, N_FOLDS = 500, 5
FINAL_SEED = 0
FOLDS = ("stratified", "plain")


def forest(seed: int) -> RandomForestClassifier:
    return RandomForestClassifier(N_TREES, class_weight="balanced", random_state=seed, n_jobs=-1)


def model_items(cut):
    """Model columns follow bank order, whatever order the cut was built in."""
    return sorted(cut, key=lambda it: it.order)


def fit_cut(X, groups, rows, seed):
    return {s: forest(seed).fit(X[rows], np.asarray(groups[s])[rows]) for s in SYSTEM_ORDER}


def predict_types(models, X):
    probas = {s: m.predict_proba(X) for s, m in models.items()}
    out_types, out_groups = [], {s: [] for s in models}
    for i in range(X.shape[0]):
        dist = {}
        for s, m in models.items():
            p = {c: float(v) for c, v in zip(m.classes_, probas[s][i])}
            dist[s] = {g: p.get(g, 0.0) for g in TAXONOMIES[s]}
            out_groups[s].append(max(TAXONOMIES[s], key=lambda g: dist[s][g]))
        out_types.append(predict_eneatype(dist)[0])
    return out_types, out_groups


def metrics(pred_types, pred_groups, types, groups):
    types = np.asarray(types); pt = np.asarray(pred_types)
    recalls = [np.mean(pt[types == t] == t) for t in np.unique(types)]
    return {"type": float(np.mean(pt == types)), "balanced": float(np.mean(recalls)),
            **{s: float(np.mean(np.asarray(pred_groups[s]) == np.asarray(groups[s]))) for s in SYSTEM_ORDER}}


def splits(kind, rep, types):
    idx = np.arange(len(types))
    if kind == "stratified":
        return StratifiedKFold(N_FOLDS, shuffle=True, random_state=rep).split(idx, types)
    return KFold(N_FOLDS, shuffle=True, random_state=rep).split(idx)


def evaluate(sample, items, sizes, reps, folds="stratified", with_random=True):
    n = len(sample.codes)
    groups = {s: np.asarray(v) for s, v in sample.groups.items()}
    types = np.asarray(sample.types)
    runs = {(size, kind): [] for size in sizes for kind in ("discrimination", "random")}
    baseline = {s: [] for s in (*SYSTEM_ORDER, "type")}
    picked = {size: {} for size in sizes}
    t0 = time.time()
    for rep in range(reps):
        oof = {key: {"t": np.zeros(n, int), "g": {s: np.empty(n, object) for s in SYSTEM_ORDER}} for key in runs}
        base_ok = {s: np.zeros(n, bool) for s in (*SYSTEM_ORDER, "type")}
        for f, (tr, te) in enumerate(splits(folds, rep, types)):
            seed = rep * 100 + f
            scores = item_scores(sample.answers, sample.groups, items, rows=tr)
            disc = select_cuts(scores, items, sizes)
            rnd = random_cuts(items, sizes, np.random.default_rng(seed))
            for size, cd, cr in zip(sorted(sizes), disc, rnd):
                for code in (it.code for it in cd):
                    picked[size][code] = picked[size].get(code, 0) + 1
                for kind, cut in (("discrimination", cd), ("random", cr)):
                    if kind == "random" and (size == len(items) or not with_random):
                        continue                       # the full bank has nothing to draw
                    mi = model_items(cut)
                    X = encode(sample.answers, mi)
                    models = fit_cut(X, groups, tr, seed)
                    pt, pg = predict_types(models, X[te])
                    oof[(size, kind)]["t"][te] = pt
                    for s in SYSTEM_ORDER:
                        oof[(size, kind)]["g"][s][te] = pg[s]
            for s, y in ((s, groups[s]) for s in SYSTEM_ORDER):   # majority-class baseline, per fold
                vals, cnt = np.unique(y[tr], return_counts=True)
                base_ok[s][te] = y[te] == vals[np.argmax(cnt)]
            vals, cnt = np.unique(types[tr], return_counts=True)       # and the most common type, per fold
            base_ok["type"][te] = types[te] == vals[np.argmax(cnt)]
        for key, o in oof.items():
            if key[1] == "random" and (key[0] == len(items) or not with_random):
                continue
            runs[key].append(metrics(o["t"], o["g"], types, groups))
        for s in base_ok:
            baseline[s].append(float(base_ok[s].mean()))
        if with_random:
            print(f"  repetition {rep + 1}/{reps} · {time.time() - t0:.0f} s", flush=True)
    return runs, baseline, picked


def permuted(sample, rng):
    """The same respondents and answers with the types shuffled across them: no answer relates to its label."""
    types = list(rng.permutation(sample.types))
    groups = {s: [TYPE_TABLE[t][s] for t in types] for s in SYSTEM_ORDER}
    return Sample(codes=sample.codes, answers=sample.answers, types=types, groups=groups)


def null_distribution(sample, items, sizes, perms, reps, folds):
    """Per cut, the median type and balanced accuracy of each permutation (selection included, as in the
    real run: with permuted labels the cuts are chosen from noise too)."""
    out = {size: {"type": [], "balanced": []} for size in sizes}
    t0 = time.time()
    for p in range(perms):
        runs, _, _ = evaluate(permuted(sample, np.random.default_rng(4000 + p)), items, sizes, reps, folds, False)
        for size in sizes:
            d = runs[(size, "discrimination")]
            out[size]["type"].append(float(np.median([r["type"] for r in d])))
            out[size]["balanced"].append(float(np.median([r["balanced"] for r in d])))
        print(f"  permutation {p + 1}/{perms} · {time.time() - t0:.0f} s", flush=True)
    return out


def stability(sample, items, reps):
    n = len(sample.codes); out = []
    for rep in range(reps):
        perm = np.random.default_rng(1000 + rep).permutation(n)
        a, b = perm[: n // 2], perm[n // 2:]
        sa = item_scores(sample.answers, sample.groups, items, rows=a)
        sb = item_scores(sample.answers, sample.groups, items, rows=b)
        out.append(spearman([sa[it.code] for it in items], [sb[it.code] for it in items]))
    return out


def summary(values):
    v = np.asarray(values)
    return {"median": float(np.median(v)), "p5": float(np.percentile(v, 5)), "p95": float(np.percentile(v, 95))}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--bank", required=True)
    ap.add_argument("--responses", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--exclude", help="optional file with respondent codes to leave out")
    ap.add_argument("--out", required=True)
    ap.add_argument("--sizes", default="40,90,145")
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--bank-version", default="v4.1.2")
    ap.add_argument("--folds", choices=FOLDS, default="stratified",
                    help="stratified by type (default, section 6 terdecies) or plain, the registered 6 ter")
    ap.add_argument("--null-perms", type=int, default=0, help="permutations of the type for the null (0: none)")
    ap.add_argument("--null-reps", type=int, default=5, help="repetitions per permutation")
    args = ap.parse_args(argv)

    items = load_bank(args.bank)
    sizes = sorted(int(x) for x in args.sizes.split(","))
    if sizes[-1] != len(items):
        raise SystemExit(f"the last cut must be the full bank ({len(items)} items)")
    sample = load_sample(args.responses, args.labels, items, read_list(args.exclude))
    n = len(sample.codes)
    counts = np.bincount(sample.types, minlength=10)[1:]
    print(f"bank {args.bank_version}: {len(items)} items · respondents with a type: {n} · "
          f"types " + " · ".join(f"{t}×{c}" for t, c in enumerate(counts, 1) if c), flush=True)

    print(f"\n1 · evaluation ({N_FOLDS} {args.folds} folds × {args.reps} repetitions)", flush=True)
    runs, baseline, picked = evaluate(sample, items, sizes, args.reps, args.folds)
    null = None
    if args.null_perms:
        print(f"\n1b · null: type permuted across respondents ({args.null_perms} × {args.null_reps} repetitions)", flush=True)
        null = null_distribution(sample, items, sizes, args.null_perms, args.null_reps, args.folds)
    stab = stability(sample, items, args.reps)
    type_base = float(counts.max() / n)

    report = {"bank_version": args.bank_version, "respondents": n, "folds": N_FOLDS, "fold_kind": args.folds,
              "repetitions": args.reps,
              "baseline": {"type_most_common": type_base, "chance": 1 / 9,
                           "type_most_common_in_fold": summary(baseline.pop("type")),
                           **{s: summary(v) for s, v in baseline.items()}},
              "ranking_split_half_spearman": summary(stab), "cuts": []}
    lines = [f"bank {args.bank_version} · n={n} · {N_FOLDS}×{args.reps} {args.folds} · type baseline {type_base:.0%} "
             f"(in fold: {report['baseline']['type_most_common_in_fold']['median']:.0%}) · chance 11%",
             f"ranking stability (split-half Spearman): median {np.median(stab):.2f} "
             f"[{np.percentile(stab, 5):.2f}–{np.percentile(stab, 95):.2f}]", ""]
    for size in sizes:
        d = runs[(size, "discrimination")]
        entry = {"size": size, "estimated_type_accuracy": float(np.median([r["type"] for r in d])),
                 "discrimination": {k: summary([r[k] for r in d]) for k in d[0]}}
        line = (f"cut {size:3}: type {np.median([r['type'] for r in d]):.0%} "
                f"[{np.percentile([r['type'] for r in d], 5):.0%}–{np.percentile([r['type'] for r in d], 95):.0%}] · "
                f"balanced {np.median([r['balanced'] for r in d]):.2f} · "
                + " ".join(f"{s[:5]} {np.median([r[s] for r in d]):.0%}" for s in SYSTEM_ORDER))
        r = runs[(size, "random")]
        if r:
            diff = np.array([a["type"] - b["type"] for a, b in zip(d, r)])
            entry["random_control"] = {k: summary([x[k] for x in r]) for k in r[0]}
            entry["discrimination_minus_random_type"] = {**summary(diff), "reps_better": int((diff > 0).sum()),
                                                         "reps_worse": int((diff < 0).sum())}
            line += (f"\n          random {np.median([x['type'] for x in r]):.0%} · paired Δ {np.median(diff):+.1%} "
                     f"(better in {(diff > 0).sum()}/{len(diff)}, worse in {(diff < 0).sum()})")
        if null:
            nt, nb = np.asarray(null[size]["type"]), np.asarray(null[size]["balanced"])
            rt, rb = entry["estimated_type_accuracy"], float(np.median([r["balanced"] for r in d]))
            entry["null"] = {"permutations": args.null_perms, "repetitions": args.null_reps,
                             "type": summary(nt), "balanced": summary(nb),
                             "p_type": float((1 + (nt >= rt).sum()) / (len(nt) + 1)),
                             "p_balanced": float((1 + (nb >= rb).sum()) / (len(nb) + 1))}
            line += (f"\n          null (type permuted): type {np.median(nt):.0%} (p95 {np.percentile(nt, 95):.0%}) · "
                     f"balanced {np.median(nb):.2f} (p95 {np.percentile(nb, 95):.2f}) · "
                     f"p type {entry['null']['p_type']:.3f} · p balanced {entry['null']['p_balanced']:.3f}")
        freq = sorted(picked[size].values(), reverse=True)
        entry["items_always_selected"] = sum(v == N_FOLDS * args.reps for v in freq)
        report["cuts"].append(entry); lines.append(line)
    print("\n" + "\n".join(lines), flush=True)

    print("\n2 · final models (all respondents)", flush=True)
    scores = item_scores(sample.answers, sample.groups, items)
    cuts = select_cuts(scores, items, sizes)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    version = f"rf-cuts-{args.bank_version}-n{n}-{date.today().isoformat()}"[:64]
    manifest = {"model_version": version, "bank_version": args.bank_version, "respondents": n,
                "sklearn": sklearn.__version__, "numpy": np.__version__, "trees": N_TREES, "seed": FINAL_SEED,
                "selection": "bias-corrected Cramér's V with the respondent's group, mean over the four systems",
                "encoding": "scenario: one-hot Qxxx_o1..o3 · Likert: integer Qxxx, 1..5",
                "cuts": []}
    groups = {s: np.asarray(v) for s, v in sample.groups.items()}
    prev = []
    for size, cut in zip(sizes, cuts):
        mi = model_items(cut)
        X = encode(sample.answers, mi)
        models = fit_cut(X, groups, np.arange(n), FINAL_SEED)
        d = out / f"cut_{size:03d}"; d.mkdir(exist_ok=True)
        for s, m in models.items():
            joblib.dump(Pipeline([("rf", m)]), d / f"{s}.joblib")
        manifest["cuts"].append({"size": size, "directory": d.name,
                                 "model_items": [it.code for it in mi], "columns": columns(mi),
                                 "serve_new_items": [it.code for it in serve_order(cut, prev, scores)]})
        prev = cut
        print(f"  cut {size}: {len(mi)} items · {X.shape[1]} columns · saved in {d}", flush=True)
    report["model_version"] = version
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "precision_by_items.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "evaluation.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nmodel version {version} · scikit-learn {sklearn.__version__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
