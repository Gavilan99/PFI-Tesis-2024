"""The classification seam: what every classifier backend receives and what it must return.

A backend takes the answers of a closed attempt and returns, for each of the four grouping systems,
the predicted group and its probability distribution; the eneatype with its confidence margin; and
the model version that produced them. Which backend runs is configuration (`CLASSIFIER_BACKEND`,
see `app.ml.registry`): no route and no service knows which one it is talking to.

Everything here is internal. None of it is serialized to the client: the result endpoint exposes
only the eneatype and the description.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from numbers import Real
from typing import Protocol

from app.db.models.enums import QuestionType
from app.ml.config import TAXONOMIES, TYPE_TABLE
from app.ml.intersection import predict_eneatype


@dataclass(frozen=True)
class Answer:
    """One answered item, with its answer key already resolved by the server."""

    question_id: uuid.UUID
    option_id: uuid.UUID
    grouping_system: str
    question_type: QuestionType
    group_label: str
    # The chosen option's position in the bank's order, 1-based, and how many options the item has.
    # For a Likert item the bank's order is the scale: the last option is maximum agreement.
    option_position: int
    option_count: int


@dataclass(frozen=True)
class SystemPrediction:
    grouping_system: str
    predicted_group: str
    probabilities: dict[str, float]


@dataclass(frozen=True)
class Classification:
    systems: dict[str, SystemPrediction]
    eneatype: int
    confidence_margin: float
    model_version: str


class Classifier(Protocol):
    model_version: str

    def classify(self, answers: Sequence[Answer]) -> Classification: ...


class InvalidClassification(ValueError):
    """A backend returned something that does not fit the seam. Nothing of it is stored."""


def predicted_group(system: str, distribution: Mapping[str, Real]) -> str:
    """The most probable group. A tie goes to the group listed first in the canonical vocabulary
    (`GROUPS_BY_SYSTEM`): `max` keeps the first of equal values."""
    return max(TAXONOMIES[system], key=lambda group: distribution[group])


def from_distributions(distributions: Mapping[str, Mapping[str, Real]], model_version: str) -> Classification:
    """Four distributions to a full classification, through the shared intersection layer.

    Used by every backend that predicts the four systems and lets the canonical table decide the
    eneatype (`stub`, `trained`). The distributions may be exact fractions: the intersection keeps
    them exact, so ties are decided by the documented rule and not by rounding.
    """
    eneatype, _, margin = predict_eneatype({system: dict(d) for system, d in distributions.items()})
    return Classification(
        systems=system_predictions(distributions),
        eneatype=eneatype,
        confidence_margin=float(margin),
        model_version=model_version,
    )


def system_predictions(distributions: Mapping[str, Mapping[str, Real]]) -> dict[str, SystemPrediction]:
    return {
        system: SystemPrediction(
            grouping_system=system,
            predicted_group=predicted_group(system, distributions[system]),
            probabilities={group: float(distributions[system][group]) for group in TAXONOMIES[system]},
        )
        for system in TAXONOMIES
    }


def validate(classification: Classification) -> Classification:
    """Refuse an output that does not fit the seam, before anything is written."""
    if not isinstance(classification, Classification):
        raise InvalidClassification(f"expected a Classification, got {type(classification).__name__}")
    if set(classification.systems) != set(TAXONOMIES):
        raise InvalidClassification(f"systems {sorted(classification.systems)} are not the four of the vocabulary")
    for system, prediction in classification.systems.items():
        groups = TAXONOMIES[system]
        if prediction.grouping_system != system:
            raise InvalidClassification(f"{system}: prediction labelled {prediction.grouping_system}")
        if prediction.predicted_group not in groups:
            raise InvalidClassification(f"{system}: unknown group {prediction.predicted_group!r}")
        if set(prediction.probabilities) != set(groups):
            raise InvalidClassification(f"{system}: probabilities are not over its three groups")
        if any(not 0.0 <= p <= 1.0 for p in prediction.probabilities.values()):
            raise InvalidClassification(f"{system}: a probability is outside [0, 1]")
        if abs(sum(prediction.probabilities.values()) - 1.0) > 1e-6:
            raise InvalidClassification(f"{system}: probabilities do not add up to 1")
    if classification.eneatype not in TYPE_TABLE:
        raise InvalidClassification(f"eneatype {classification.eneatype!r} is not 1-9")
    if not classification.confidence_margin >= 0:
        raise InvalidClassification("the confidence margin is negative or not a number")
    if not classification.model_version or len(classification.model_version) > 64:
        raise InvalidClassification("the model version is empty or longer than its column")
    return classification
