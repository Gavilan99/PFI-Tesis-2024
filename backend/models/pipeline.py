"""End-to-end sanity check: synthetic data -> train 4 classifiers -> intersect
-> report accuracy against known synthetic labels.

Run as a module from `backend/`: `python -m models.pipeline`

This proves the architecture wires together correctly. It does NOT validate
real-world accuracy -- that only means something once
`tests/synthetic_data.py` is replaced with the real dataset (due 2026-09-04).
"""

from __future__ import annotations

from sklearn.model_selection import train_test_split

from models.classifiers import train_all_classifiers
from models.config import TAXONOMIES, validate_type_table
from models.intersection import predict_eneatypes_batch
from models.tests.synthetic_data import generate_synthetic_dataset


def main():
    validate_type_table()

    eneatypes, X_by_taxonomy, y_by_taxonomy = generate_synthetic_dataset(n_samples=400)

    # Single split shared across all 4 taxonomies + the ground-truth eneatypes,
    # so we can evaluate the combined pipeline on the same held-out respondents.
    indices = list(range(len(eneatypes)))
    train_idx, test_idx = train_test_split(indices, test_size=0.25, random_state=42, stratify=eneatypes)

    X_train = {t: X_by_taxonomy[t][train_idx] for t in TAXONOMIES}
    y_train = {t: y_by_taxonomy[t][train_idx] for t in TAXONOMIES}
    X_test = {t: X_by_taxonomy[t][test_idx] for t in TAXONOMIES}
    eneatypes_test = eneatypes[test_idx]

    classifiers = train_all_classifiers(X_train, y_train, TAXONOMIES)

    proba_lists_by_taxonomy = {
        taxonomy: clf.predict_proba(X_test[taxonomy]) for taxonomy, clf in classifiers.items()
    }
    predictions = predict_eneatypes_batch(proba_lists_by_taxonomy)

    correct = sum(1 for (pred, _, _), true in zip(predictions, eneatypes_test) if pred == true)
    accuracy = correct / len(eneatypes_test)

    print(f"Synthetic sanity-check accuracy: {accuracy:.2%} ({correct}/{len(eneatypes_test)})")
    print("Sample predictions (predicted, score, margin, true):")
    for (pred, score, margin), true in list(zip(predictions, eneatypes_test))[:10]:
        flag = "OK" if pred == true else "MISS"
        print(f"  [{flag}] predicted={pred} score={score:.2f} margin={margin:.2f} true={true}")


if __name__ == "__main__":
    main()
