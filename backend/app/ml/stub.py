"""`CLASSIFIER_BACKEND=stub`: a deterministic count, not a model.

The four distributions come from counting answers by group (`app.ml.tally`); the eneatype comes from
the shared intersection layer over the canonical table. Its version, `stub-tally-1`, is stored in
every prediction it makes, so any result it produced can be told apart in the database forever.

Ties, both documented where they are decided:
- the predicted group of a system: the group listed first in the canonical vocabulary;
- the eneatype: the lowest type number (`app.ml.intersection.predict_eneatype`).

Imports nothing from scikit-learn.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.ml.classification import Answer, Classification, from_distributions
from app.ml.tally import tally_distributions

STUB_MODEL_VERSION = "stub-tally-1"


class StubClassifier:
    model_version = STUB_MODEL_VERSION

    def classify(self, answers: Sequence[Answer]) -> Classification:
        return from_distributions(tally_distributions(answers), self.model_version)


def build_stub(config) -> StubClassifier:
    return StubClassifier()
