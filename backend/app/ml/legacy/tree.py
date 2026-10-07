"""`CLASSIFIER_BACKEND=legacy_tree`: the project's 2024 decision tree, the model of the original document.

Input: one group per grouping system. The winner of each system comes from the same count the stub
uses (`app.ml.tally`, same tie rule), translated to the old dataset's one-hot columns with the
explicit map below. The column order is read from the model, never assumed.

Output: the eneatype the tree predicts, without going through the intersection layer; that is the
point of this backend. The margin is the gap between the tree's two highest class probabilities;
a tie between classes goes to the lowest eneatype. The four `classifier_predictions` rows are still
the count's distributions.

The tree and the canonical table do not always agree: the 2024 dataset has combinations that
contradict the table. That is measured and written down (`app/ml/README.md`), not corrected here.

scikit-learn is imported only when this backend is built.
"""

from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from pathlib import Path

from app.config import ConfigError
from app.ml.classification import Answer, Classification, predicted_group, system_predictions
from app.ml.config import TAXONOMIES
from app.ml.tally import tally_distributions

LEGACY_MODEL_VERSION = "legacy-tree-1"
MODEL_PATH = Path(__file__).resolve().parent / "decision_tree_model.pkl"

# Canonical (grouping_system, group_label) -> the 2024 dataset's one-hot column.
LEGACY_COLUMNS: dict[tuple[str, str], str] = {
    ("hornevian", "assertive"): "Hornevian_Assertive",
    ("hornevian", "compliant"): "Hornevian_Compliant",
    ("hornevian", "withdrawn"): "Hornevian_Withdrawn",
    ("harmonic", "positive_outlook"): "Harmonic_Positive",
    ("harmonic", "competency"): "Harmonic_Competency",
    ("harmonic", "reactive"): "Harmonic_Reactive",
    ("object_relations", "attachment"): "Harmony_Attachment",
    ("object_relations", "frustration"): "Harmony_Frustration",
    ("object_relations", "rejection"): "Harmony_Rejection",
    ("intelligence_centers", "heart"): "Triad_Feeling",
    ("intelligence_centers", "gut"): "Triad_Intuition",
    ("intelligence_centers", "head"): "Triad_Thought",
}


class LegacyTreeClassifier:
    model_version = LEGACY_MODEL_VERSION

    def __init__(self, model) -> None:
        self._model = model
        self._columns = [str(name) for name in model.feature_names_in_]
        expected = set(LEGACY_COLUMNS.values())
        if set(self._columns) != expected or len(self._columns) != len(expected):
            raise ConfigError(
                "El árbol de 2024 no tiene las 12 columnas esperadas del dataset viejo: "
                f"tiene {self._columns}."
            )
        self._classes = [int(c) for c in model.classes_]

    def predict_from_groups(self, groups: Mapping[str, str]) -> tuple[int, float]:
        """One group per system -> (eneatype, margin between the two most probable classes)."""
        import numpy as np

        active = {LEGACY_COLUMNS[(system, groups[system])] for system in TAXONOMIES}
        X = np.array([[1.0 if column in active else 0.0 for column in self._columns]])
        with warnings.catch_warnings():
            # Fitted on a DataFrame, fed an array whose columns were put in the model's own order.
            warnings.filterwarnings("ignore", message="X does not have valid feature names")
            proba = self._model.predict_proba(X)[0]
        ranked = sorted(range(len(proba)), key=lambda i: (-proba[i], self._classes[i]))
        top, runner_up = ranked[0], ranked[1]
        return self._classes[top], float(proba[top] - proba[runner_up])

    def classify(self, answers: Sequence[Answer]) -> Classification:
        distributions = tally_distributions(answers)
        groups = {system: predicted_group(system, distributions[system]) for system in TAXONOMIES}
        eneatype, margin = self.predict_from_groups(groups)
        return Classification(
            systems=system_predictions(distributions),
            eneatype=eneatype,
            confidence_margin=margin,
            model_version=self.model_version,
        )


def load_model(path: Path = MODEL_PATH):
    """The pickled tree. A version mismatch with the installed scikit-learn is a warning on load:
    it is turned into an error, so a tree that might predict differently never starts."""
    import joblib
    from sklearn.exceptions import InconsistentVersionWarning

    if not path.is_file():
        raise ConfigError(f"CLASSIFIER_BACKEND=legacy_tree necesita el árbol de 2024 y no está en {path}.")
    with warnings.catch_warnings():
        warnings.simplefilter("error", InconsistentVersionWarning)
        try:
            return joblib.load(path)
        except InconsistentVersionWarning as warning:
            raise ConfigError(
                f"El árbol de 2024 ({path.name}) se guardó con otra versión de scikit-learn: {warning}. "
                "Reentrenalo con `python -m app.ml.legacy.train --output ...`."
            ) from None


def build_legacy_tree(config) -> LegacyTreeClassifier:
    return LegacyTreeClassifier(load_model())
