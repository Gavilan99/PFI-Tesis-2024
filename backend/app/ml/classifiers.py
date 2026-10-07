"""One classifier per conjunto de triadas.

Model choice (Random Forest) and rationale are documented in
`01 In Progress/(C) 2026-08-11 4-classifier ML architecture design.md`:
small/categorical questionnaire data, 3-class target per taxonomy, needs to
stay interpretable (SHAP, not raw Gini importance) and cheap to tune within
the project deadline.
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestClassifier


class TaxonomyClassifier:
    """Wraps a RandomForestClassifier for a single taxonomy (conjunto de triadas)."""

    def __init__(self, taxonomy: str, classes: list[str], random_state: int = 42):
        self.taxonomy = taxonomy
        self.classes = classes
        self.model = RandomForestClassifier(
            n_estimators=300,
            max_depth=None,  # let trees grow; bagging controls variance instead
            min_samples_split=10,  # mirrors the original thesis DecisionTreeClassifier setting
            class_weight="balanced",  # questionnaire responses are unlikely to be perfectly balanced
            random_state=random_state,
        )

    def fit(self, X: np.ndarray, y: np.ndarray) -> "TaxonomyClassifier":
        self.model.fit(X, y)
        return self

    def predict_proba(self, X: np.ndarray) -> list[dict[str, float]]:
        """Returns, per sample, a dict of {class_label: probability}."""
        proba = self.model.predict_proba(X)
        # model.classes_ may not be in the same order as self.classes -- map explicitly.
        class_order = list(self.model.classes_)
        return [
            {cls: float(row[class_order.index(cls)]) if cls in class_order else 0.0 for cls in self.classes}
            for row in proba
        ]

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)


def train_all_classifiers(X_by_taxonomy: dict[str, np.ndarray], y_by_taxonomy: dict[str, np.ndarray], taxonomies: dict[str, list[str]]) -> dict[str, TaxonomyClassifier]:
    """Train one TaxonomyClassifier per taxonomy. Each sees only its own features."""
    classifiers: dict[str, TaxonomyClassifier] = {}
    for taxonomy, classes in taxonomies.items():
        clf = TaxonomyClassifier(taxonomy, classes)
        clf.fit(X_by_taxonomy[taxonomy], y_by_taxonomy[taxonomy])
        classifiers[taxonomy] = clf
    return classifiers
