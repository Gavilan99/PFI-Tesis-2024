# `app/ml` — canonical table, intersection, classification seam

The 4-classifier architecture of `01 In Progress/(C) 2026-08-11 4-classifier ML architecture design.md`
(scaffold merged in Feature 4.0, moved here from `backend/models/` in Feature 4.1), plus the seam that
turns a closed attempt into a result.

## Files

- `config.py` — the canonical eneatype → 4-system lookup table (`TYPE_TABLE`). Its systems and groups
  are the canonical vocabulary of `app/db/models/enums.py` (`TAXONOMIES` is derived from it): one
  vocabulary, one copy of the table.
- `intersection.py` — the probability-weighted scoring layer: four distributions → eneatype + margin.
  Ties go to the lowest eneatype. The sum keeps exact fractions exact, so a tie is decided by that
  rule and not by float rounding.
- `classification.py` — **the seam.** `Answer` in; `Classification` out (per system the predicted
  group and its distribution, the eneatype, the margin, the model version). `validate` refuses an
  output that does not fit before anything is stored.
- `registry.py` — `CLASSIFIER_BACKEND` → backend. Built-ins are imported lazily; `register` adds one.
- `tally.py`, `stub.py` — `stub`. Not ML.
- `legacy/` — `legacy_tree`: the 2024 tree, its dataset and its training script.
- `trained.py` — `trained`: refuses to start (see below).
- `classifiers.py`, `pipeline.py`, `tests/synthetic_data.py` — the Random Forest scaffold and its
  synthetic sanity check. scikit-learn is imported only here and in `legacy/`.

## Backends (`CLASSIFIER_BACKEND`)

One runs at a time; switching is changing the variable and restarting. No route or service changes.
Every prediction stores its `model_version`, so a result can always be traced to what produced it.

| Value | Version | Eneatype decided by |
|---|---|---|
| `stub` (default in development and test) | `stub-tally-1` | count by group → shared intersection |
| `legacy_tree` | `legacy-tree-1` | the 2024 tree, fed the count's winning group per system |
| `trained` | — | does not start: no artifacts, and the answer → feature encoding is undecided |

In production the variable has no default: the app does not start until someone chooses.

### `stub`: the count

Per system: a scenario answer adds 1 to the chosen option's group; a Likert answer adds
`(position − 1) / (options − 1)` to its target group (option 1 = minimum agreement adds 0, option 5 =
maximum adds 1, the same as a scenario answer). Counts are normalized; a system with nothing counted
is uniform. Exact fractions throughout: same answers, any order, same result.

Ties: within a system, the group listed first in the vocabulary is the predicted group (it only
labels the row; the full distribution is what the intersection uses). Between eneatypes, the lowest
number.

### `legacy_tree`: the 2024 decision tree

`legacy/decision_tree_model.pkl` is the original 2024 file, byte for byte. It was saved with
scikit-learn 1.5.2, the version this service pins, and loads without warnings, so it was **not
retrained**. Loading turns a version-mismatch warning into a startup error.

`python -m app.ml.legacy.train` retrains it from `legacy/dataset.csv` with the original split,
hyperparameters and seed, prints accuracy 0.94 and 5-fold CV 0.94 (as the 2024 document reports),
and confirms the tree it trains is identical to the shipped one. It writes nothing without `--output`.

Input: the count's winning group per system, mapped explicitly to the old columns
(`hornevian`→`Hornevian`; `harmonic`→`Harmonic`, `positive_outlook`→`Positive`;
`object_relations`→`Harmony`; `intelligence_centers`→`Triad`, `heart`/`gut`/`head` →
`Feeling`/`Intuition`/`Thought`). Column order is read from the model.

#### Measured against the canonical table (Feature 4.1)

Over the 81 possible combinations of one group per system:

- **The tree agrees with the canonical table (nearest type by the intersection) in 77 of 81**, and
  in all 9 combinations that are exactly a row of the table. It differs in 4:

  | intelligence_centers | hornevian | harmonic | object_relations | canonical | tree |
  |---|---|---|---|---|---|
  | gut | withdrawn | competency | attachment | 9 | 1 |
  | heart | compliant | competency | attachment | 3 | 1 |
  | heart | compliant | reactive | frustration | 4 | 6 |
  | head | withdrawn | positive_outlook | frustration | 7 | 9 |

- **The 2024 dataset itself agrees with the canonical table in all 891 rows** (81 combinations × 11
  copies; no combination has two labels, and none is a tie under the intersection). The design
  document's note that the dataset contradicts the table compared rows only against exact table
  rows; by nearest type, it encodes the table. So the 4 disagreements are the tree's own errors on
  its training data (`max_depth=7`, `min_samples_split=10`): 77/81 ≈ 0.95, consistent with the 0.94
  it reports.

Not corrected here, on purpose.

### `trained`

Needs `intelligence_centers.joblib`, `hornevian.joblib`, `harmonic.joblib` and
`object_relations.joblib` in `CLASSIFIER_ARTIFACTS_DIR` (default `app/ml/artifacts/`). Without them
the app does not start and says so; it never falls back to the stub. With them it still refuses,
until the answer → feature encoding is defined (real bank, `NO_PREGUNTADO` proposal). When it lands
it hands four distributions to `classification.from_distributions`, the same intersection as the stub.

## Running the sanity check

From `backend/`:

```
python -m app.ml.pipeline
```

Expect ~100% against the synthetic labels: it proves the wiring, not real accuracy, since the
synthetic features are generated from the same table the pipeline recovers.

## Next steps once real data exists

1. Replace `tests/synthetic_data.py` with a real loader, outside `tests/`.
2. Define the answer → feature encoding and implement `trained` on top of `from_distributions`.
3. Grouped stratified k-fold per classifier (the 2024 tree reported 0.94).
4. Check that the real labels reconstruct `TYPE_TABLE`.
