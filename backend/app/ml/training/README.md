# `app/ml/training` — the product's classifiers: three fixed item cuts

The test is served in three fixed, nested cuts of **40, 90 and 145 items**. Every user gets the same items in the same order. After each cut the user sees the estimated accuracy and decides whether to continue. The first cut is the free tier.

Each cut has its own **four Random Forests**, one per grouping system, trained only on that cut's columns. That makes twelve models. Because each model sees only its own cut, every input is complete and no "not asked" value exists at serving time. Masking and adaptive selection are left for the v2.

Decision record: PDR *NureonAI Product Classifier and Fixed Item Cuts*. Evaluation protocol: pilot analysis plan §6 nonies.

## Files

- `bank.py` — reads the bank CSV *(one row per option)* into `Item`s in bank order. Spanish system labels are translated with the importer's table.
- `encoding.py` — **the answer → feature contract**, shared by training and inference. See below.
- `data.py` — reads the pilot data: responses, expert types and an optional exclusion list. Each respondent's group per system is derived from the type through `TYPE_TABLE`.
- `selection.py` — item scores, balanced quotas, nested cuts, the random-cut control, serving order and split-half stability.
- `train.py` — evaluation plus final models. The only entry point.

## The feature contract

For each item of a cut, in the order of `manifest.json → cuts[i].model_items` *(bank order)*:

| Item | Columns | Value |
|---|---|---|
| scenario | `Qxxx_o1`, `Qxxx_o2`, `Qxxx_o3` | one-hot of the chosen option's position |
| Likert | `Qxxx` | the chosen position, 1–5 *(1 = minimum agreement)* |

The position is the option's place in the bank's order, 1-based, which is the same as `Answer.option_position`. An item is identified by its bank code (`Q001` … `Q145`). The code's number is the item's place in the bank: `Item.order`.

**Inference:**
1. Build `{code: option_position}` from the attempt's answers.
2. Call `encoding.encode_one(positions, items_of_the_cut)`.
3. Call `predict_proba` on each of the four models of that cut *(each is a `Pipeline` with one step, `rf`; `classes_` are the canonical groups)*.
4. Hand the four distributions to `classification.from_distributions`.

A cut whose items are not all answered is an error, never a default.

## Selection

- **Item score:** the bias-corrected Cramér's V between the chosen position and the respondent's group, computed for each of the four systems and averaged. The options' `group_label` is never read; a test checks it.
- **Balance:**
	- quotas per *(grouping system, format)* stratum, proportional to the bank, by largest remainder;
	- the cut of 40 has 7 scenarios and 3 Likert items per system;
	- the quotas grow with the cut, so the cuts are nested.
- **Honest estimate:**
	- the accuracy reported for each cut comes from 5-fold cross-validation repeated 20 times, one row per person;
	- the selection is redone inside every training fold;
	- each cut is compared with **random balanced cuts of the same size** trained on the same folds;
	- the split-half stability of the ranking is reported next to it.

## Running

From `backend/`, in the backend's environment *(scikit-learn pinned in `requirements.txt`: the artifacts must be saved with the same version that loads them)*:

```
python -m app.ml.training.train \
    --bank "../research/bank/NureonAI Prototype v4.1.2.csv" \
    --responses <private data>/responses_wide.csv \
    --labels <private data>/tipificaciones_piloto.csv \
    --out app/ml/artifacts
```

The pilot data are private and never enter the repository *(see `research/README.md`)*. A full run takes about 45 minutes on a laptop; `--reps 2` gives a quick check.

## Output (`--out`)

| File | Content |
|---|---|
| `cut_040/`, `cut_090/`, `cut_145/` | `intelligence_centers.joblib`, `hornevian.joblib`, `harmonic.joblib`, `object_relations.joblib` |
| `manifest.json` | `model_version`, versions, encoding, and per cut: `model_items` *(column order)*, `columns`, and `serve_new_items` *(the items the cut adds, in the order to show them)* |
| `precision_by_items.json` | per cut: `estimated_type_accuracy` *(the number the product shows)*, per-system accuracy, balanced accuracy, the random control and the paired difference; the baselines; the ranking stability |
| `evaluation.txt` | the same, as text |

Only aggregates are written: no respondent code leaves `train.py`. The artifacts directory stays out of the repository.

**No `SelectKBest`** *(k = all columns of the cut)*: the reduction is done by the cuts, not by column selection.

An unasked item is never encoded: with fixed cuts every model receives its whole cut. The "0 in every column" encoding for an unasked item is reserved for the v2 *(masking)*.
