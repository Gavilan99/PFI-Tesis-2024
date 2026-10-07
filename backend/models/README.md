# 4-classifier ML pipeline — scaffold

Reference implementation of the architecture designed in `01 In Progress/(C) 2026-08-11 4-classifier ML architecture design.md`. Built while the questionnaire rework (due 08-31) and real dataset (due 09-04) are still blocked, so it uses synthetic data to prove the pipeline end-to-end. Swap in the real dataset later — the classifier and intersection code shouldn't need to change, only `tests/synthetic_data.py` gets replaced by a real data loader.

## Files

- `config.py` — the canonical eneatype → 4-taxonomy lookup table (verified against standard Enneagram triad theory) and taxonomy class labels.
- `classifiers.py` — `TaxonomyClassifier`: thin wrapper around `RandomForestClassifier` (per the model research in the task file — entropy-friendly defaults, `class_weight="balanced"`, tuned for small/categorical data).
- `intersection.py` — the probability-weighted scoring layer that combines the 4 classifiers' outputs into a final eneatype prediction + confidence margin.
- `pipeline.py` — end-to-end script: generate synthetic data → train 4 classifiers → run intersection → report accuracy against known synthetic labels. Run this directly to sanity-check the whole architecture.
- `tests/synthetic_data.py` — **test fixture, not real data.** Generates a placeholder dataset consistent with the canonical table, so the pipeline can be exercised before real questionnaire data exists. Only `pipeline.py` (and tests) should import it. **Delete/replace once real data lands.**

## Running the sanity check

From `backend/`:

```
pip install -r requirements.txt
python -m models.pipeline
```

Expect ~100% accuracy against the synthetic labels — that's expected and not a real metric, since the synthetic features are generated directly from the same lookup table the pipeline is trying to recover. It only proves the wiring (data shapes, classifier training, intersection scoring) is correct end-to-end.

## Next steps once real data exists

1. Replace `tests/synthetic_data.py` with a real loader (reads the actual dataset, applies the real questionnaire-item → taxonomy feature mapping), living outside `tests/`.
2. Re-run `pipeline.py` as-is — it should just work with real `X`/`y` in the same shape.
3. Add the stratified k-fold cross-validation evaluation (the thesis's original model reported 0.94 CV accuracy — worth the same rigor here, per each classifier).
4. Sanity-check the real dataset's labels reconstruct `config.TYPE_TABLE` correctly (flagged as an open item in the design doc).
