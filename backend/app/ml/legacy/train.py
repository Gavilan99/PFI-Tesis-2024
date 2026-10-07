"""Retrain the 2024 decision tree: `python -m app.ml.legacy.train [--output PATH]`, from `backend/`.

A version of the project's original `scr/decisionTree.py` (left untouched at the repo root) with its
paths relative to this folder. Same data, same one-hot encoding, same split, same hyperparameters,
same seed. It prints the same two metrics the 2024 document reports (accuracy and 5-fold
cross-validation, 0.94 both) and says whether the tree it trains is identical to the shipped one.

Left out on purpose: the plots and the Graphviz export of the original (matplotlib, seaborn and
graphviz are not dependencies of this service), and pandas, which the original used only for
`read_csv` and `get_dummies`. The encoding is reproduced below column by column, in pandas' order.

Writes nothing unless `--output` is given. The shipped artifact, `decision_tree_model.pkl`, is the
original 2024 file, copied byte for byte: it loads clean with the scikit-learn version this service
pins, so it was not retrained.
"""

from __future__ import annotations

import argparse
import csv
import sys
import warnings
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.tree import DecisionTreeClassifier

HERE = Path(__file__).resolve().parent
DATASET_PATH = HERE / "dataset.csv"
MODEL_PATH = HERE / "decision_tree_model.pkl"

# The original: pd.get_dummies(df, columns=['Hornevian', 'Harmonic', 'Harmony', 'Triad']).
CATEGORICAL_COLUMNS = ("Hornevian", "Harmonic", "Harmony", "Triad")
TARGET_COLUMN = "Result"


def load_dataset(path: Path = DATASET_PATH) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """X as pandas' get_dummies would build it: per column, in the order given, one 0/1 column per
    distinct value, values sorted; named `<column>_<value>`."""
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    feature_names = [
        f"{column}_{value}"
        for column in CATEGORICAL_COLUMNS
        for value in sorted({row[column] for row in rows})
    ]
    index = {name: i for i, name in enumerate(feature_names)}
    X = np.zeros((len(rows), len(feature_names)))
    for r, row in enumerate(rows):
        for column in CATEGORICAL_COLUMNS:
            X[r, index[f"{column}_{row[column]}"]] = 1
    y = np.array([int(row[TARGET_COLUMN]) for row in rows])
    return X, y, feature_names


def train(X: np.ndarray, y: np.ndarray) -> tuple[DecisionTreeClassifier, float, float]:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    dtc = DecisionTreeClassifier(
        max_depth=7, min_samples_split=10, class_weight="balanced", criterion="entropy", random_state=42
    )
    dtc.fit(X_train, y_train)
    accuracy = accuracy_score(y_test, dtc.predict(X_test))
    cv_scores = cross_val_score(dtc, X, y, cv=StratifiedKFold(n_splits=5))
    return dtc, accuracy, cv_scores.mean()


def same_tree(a: DecisionTreeClassifier, b: DecisionTreeClassifier) -> bool:
    ta, tb = a.tree_, b.tree_
    return (
        ta.node_count == tb.node_count
        and np.array_equal(ta.feature, tb.feature)
        and np.allclose(ta.threshold, tb.threshold)
        and np.allclose(ta.value, tb.value)
        and np.array_equal(a.classes_, b.classes_)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reentrena el árbol de decisión de 2024.")
    parser.add_argument("--output", type=Path, help="Dónde guardar el árbol entrenado. Sin esto no se guarda nada.")
    args = parser.parse_args(argv)

    X, y, feature_names = load_dataset()
    # Fitted on a plain array, unlike the original's DataFrame: the names are set by hand below, so
    # the saved artifact carries them like the 2024 one does.
    dtc, accuracy, cv_accuracy = train(X, y)
    dtc.feature_names_in_ = np.array(feature_names, dtype=object)

    print(f"Columnas: {feature_names}")
    print(f"Accuracy: {accuracy:.2f}")
    print(f"Cross-Validation Accuracy: {cv_accuracy:.2f}")

    with warnings.catch_warnings():
        warnings.simplefilter("error")  # a version mismatch would be a warning: make it loud
        shipped = joblib.load(MODEL_PATH)
    identical = same_tree(dtc, shipped) and list(shipped.feature_names_in_) == feature_names
    print(f"Idéntico al artefacto de 2024 ({MODEL_PATH.name}): {'sí' if identical else 'NO'}")

    if args.output:
        joblib.dump(dtc, args.output)
        print(f"Guardado en {args.output}")
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")  # readable when piped on Windows (cp1252 by default)
    raise SystemExit(main())
