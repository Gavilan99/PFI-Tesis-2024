"""TEST FIXTURE ONLY -- not real data.

Placeholder data generator, used only until the real questionnaire dataset
(due 2026-09-04) exists. Produces feature vectors that are noisily correlated
with each taxonomy's true group label, so the pipeline can be trained and
sanity-checked end-to-end before real data is available.

This module must never be imported by application/production code (only by
`models.pipeline` for the wiring sanity check, or by tests). Replace it with
a real loader once the dataset lands. Nothing in `models/classifiers.py`,
`models/intersection.py`, or `models/pipeline.py` should need to change --
they only expect X (n_samples, n_features) and y (n_samples,) per taxonomy.
"""

from __future__ import annotations

import numpy as np

from models.config import TAXONOMIES, TYPE_TABLE


def generate_synthetic_dataset(n_samples: int = 300, n_features_per_taxonomy: int = 10, noise: float = 0.35, random_state: int = 42):
    """Generate a synthetic dataset consistent with TYPE_TABLE.

    For each synthetic respondent: pick a true eneatype uniformly at random,
    look up its 4 group labels, then generate noisy features per taxonomy
    that are weakly predictive of the true group (mimics real questionnaire
    answers correlating imperfectly with the underlying trait).

    Returns:
        eneatypes: (n_samples,) array of true eneatypes, 1-9 -- ground truth,
            only used for evaluating the pipeline, never fed to the classifiers.
        X_by_taxonomy: dict[taxonomy_name] -> (n_samples, n_features) float array.
        y_by_taxonomy: dict[taxonomy_name] -> (n_samples,) array of string labels.
    """
    rng = np.random.default_rng(random_state)
    types = list(TYPE_TABLE.keys())
    eneatypes = rng.choice(types, size=n_samples)

    X_by_taxonomy: dict[str, np.ndarray] = {}
    y_by_taxonomy: dict[str, np.ndarray] = {}

    for taxonomy, classes in TAXONOMIES.items():
        y = np.array([TYPE_TABLE[t][taxonomy] for t in eneatypes])
        y_by_taxonomy[taxonomy] = y

        # Each class gets a fixed random "center" in feature space; samples are
        # that center plus noise, so a classifier can learn the mapping but it
        # isn't trivially separable -- mimics real, imperfect questionnaire signal.
        class_centers = {c: rng.normal(loc=0.0, scale=1.0, size=n_features_per_taxonomy) for c in classes}
        X = np.array([class_centers[label] + rng.normal(scale=noise, size=n_features_per_taxonomy) for label in y])
        X_by_taxonomy[taxonomy] = X

    return eneatypes, X_by_taxonomy, y_by_taxonomy
