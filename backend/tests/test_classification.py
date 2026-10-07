"""The classification seam and its three built-in backends, without the database.

stub: a count by group plus the canonical table, deterministic. legacy_tree: the 2024 tree.
trained: refuses to start. A new backend enters by configuration through the registry.
"""

import itertools
import random
import subprocess
import sys
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

from app import create_app
from app.config import ConfigError, get_config
from app.ml import registry
from app.ml.classification import (
    Classification,
    InvalidClassification,
    SystemPrediction,
    from_distributions,
    predicted_group,
    validate,
)
from app.ml.config import TAXONOMIES, TYPE_TABLE
from app.ml.legacy.tree import LEGACY_COLUMNS, LEGACY_MODEL_VERSION, build_legacy_tree
from app.ml.stub import STUB_MODEL_VERSION, StubClassifier
from app.ml.tally import tally_distributions
from tests.classifier_helpers import answers_for_groups, likert, scenario

BACKEND = Path(__file__).resolve().parents[1]
ALL_COMBINATIONS = [
    dict(zip(TAXONOMIES, groups)) for groups in itertools.product(*TAXONOMIES.values())
]


@pytest.fixture(scope="module")
def legacy():
    return build_legacy_tree(get_config("test"))


def _random_answers(rng: random.Random, per_system: int = 5) -> list:
    answers = []
    for system, groups in TAXONOMIES.items():
        for _ in range(per_system):
            if rng.random() < 0.8:
                answers.append(scenario(system, rng.choice(groups)))
            else:
                answers.append(likert(system, rng.choice(groups), rng.randint(1, 5)))
    return answers


# --- the count ----------------------------------------------------------------------------------


def test_a_scenario_answer_adds_one_to_the_chosen_group():
    distributions = tally_distributions(
        [scenario("hornevian", "assertive"), scenario("hornevian", "assertive"), scenario("hornevian", "withdrawn")]
    )
    assert distributions["hornevian"] == {
        "assertive": Fraction(2, 3), "compliant": Fraction(0), "withdrawn": Fraction(1, 3),
    }


@pytest.mark.parametrize(("position", "weight"), [(1, 0), (2, Fraction(1, 4)), (3, Fraction(1, 2)), (5, 1)])
def test_a_likert_answer_adds_to_its_target_by_the_position_chosen(position, weight):
    """Option 5 is maximum agreement and weighs like a scenario answer; option 1 adds nothing."""
    distributions = tally_distributions(
        [likert("harmonic", "reactive", position), scenario("harmonic", "competency")]
    )
    total = 1 + weight
    assert distributions["harmonic"] == {
        "positive_outlook": 0, "competency": 1 / total, "reactive": weight / total,
    }


def test_a_system_without_answers_is_uniform():
    distributions = tally_distributions([scenario("hornevian", "assertive")])
    for system in ("intelligence_centers", "harmonic", "object_relations"):
        assert set(distributions[system].values()) == {Fraction(1, 3)}


def test_a_system_with_only_minimum_agreement_is_uniform():
    distributions = tally_distributions([likert("object_relations", "rejection", 1)] * 4)
    assert set(distributions["object_relations"].values()) == {Fraction(1, 3)}


def test_an_answer_outside_its_system_is_refused():
    with pytest.raises(ValueError):
        tally_distributions([scenario("hornevian", "gut")])


# --- ties, documented ---------------------------------------------------------------------------


def test_a_tie_between_groups_goes_to_the_first_of_the_vocabulary():
    assert predicted_group("intelligence_centers", {"gut": 0.5, "heart": 0, "head": 0.5}) == "gut"
    assert predicted_group("harmonic", {"positive_outlook": 0, "competency": 0.5, "reactive": 0.5}) == "competency"


def test_a_tie_between_eneatypes_goes_to_the_lowest_number():
    result = StubClassifier().classify([])  # everything uniform: the nine types tie
    assert result.eneatype == 1
    assert result.confidence_margin == 0


# --- stub ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("eneatype", TYPE_TABLE)
def test_each_eneatype_comes_out_of_its_own_groups(eneatype):
    result = StubClassifier().classify(answers_for_groups(TYPE_TABLE[eneatype]))
    assert result.eneatype == eneatype
    assert {s: p.predicted_group for s, p in result.systems.items()} == TYPE_TABLE[eneatype]


def test_the_same_answers_give_the_same_result_always_and_in_any_order():
    rng = random.Random(7)
    stub = StubClassifier()
    for _ in range(50):
        answers = _random_answers(rng)
        first = stub.classify(answers)
        for _ in range(10):
            assert stub.classify(rng.sample(answers, len(answers))) == first
        assert StubClassifier().classify(list(answers)) == first


def test_the_stub_output_fits_the_seam_and_names_itself():
    result = validate(StubClassifier().classify(_random_answers(random.Random(1))))
    assert result.model_version == STUB_MODEL_VERSION == "stub-tally-1"
    assert set(result.systems) == set(TAXONOMIES)


def test_the_stub_path_does_not_load_scikit_learn():
    """In a fresh interpreter: build the app with the stub, classify, and look at what got imported."""
    code = (
        "import os, sys\n"
        "os.environ.update(APP_ENV='test', CLASSIFIER_BACKEND='stub')\n"
        "from app import create_app\n"
        "app = create_app('test')\n"
        "from tests.classifier_helpers import answers_for_groups\n"
        "from app.ml.config import TYPE_TABLE\n"
        "assert app.extensions['classifier'].classify(answers_for_groups(TYPE_TABLE[4])).eneatype == 4\n"
        "loaded = sorted(m for m in sys.modules if m.split('.')[0] in ('sklearn', 'joblib', 'scipy'))\n"
        "print(loaded)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=BACKEND, capture_output=True, text=True, timeout=120
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines()[-1] == "[]"  # the app logs to stdout first


# --- legacy_tree --------------------------------------------------------------------------------


def test_the_legacy_map_covers_the_twelve_canonical_groups(legacy):
    assert set(LEGACY_COLUMNS) == {(s, g) for s, groups in TAXONOMIES.items() for g in groups}
    assert sorted(LEGACY_COLUMNS.values()) == sorted(legacy._columns)


@pytest.mark.parametrize("groups", ALL_COMBINATIONS, ids=lambda g: "-".join(g.values()))
def test_legacy_tree_gives_an_eneatype_for_every_one_of_the_81_combinations(legacy, groups):
    result = validate(legacy.classify(answers_for_groups(groups)))
    assert 1 <= result.eneatype <= 9
    assert result.model_version == LEGACY_MODEL_VERSION == "legacy-tree-1"
    assert {s: p.predicted_group for s, p in result.systems.items()} == groups
    assert 0 <= result.confidence_margin <= 1


def test_legacy_tree_decides_the_eneatype_itself_not_the_intersection(legacy):
    """Where the 2024 tree contradicts the canonical table, the tree's answer is the one returned."""
    disagreements = 0
    for groups in ALL_COMBINATIONS:
        answers = answers_for_groups(groups)
        tree, _ = legacy.predict_from_groups(groups)
        assert legacy.classify(answers).eneatype == tree
        disagreements += tree != StubClassifier().classify(answers).eneatype
    assert disagreements > 0  # measured, not fixed: see app/ml/README.md


def test_legacy_tree_is_deterministic(legacy):
    rng = random.Random(3)
    for _ in range(20):
        answers = _random_answers(rng)
        assert legacy.classify(answers) == legacy.classify(rng.sample(answers, len(answers)))


# --- trained ------------------------------------------------------------------------------------


def test_starting_with_trained_and_no_artifacts_fails_and_says_so(monkeypatch, tmp_path):
    monkeypatch.setenv("CLASSIFIER_BACKEND", "trained")
    monkeypatch.setenv("CLASSIFIER_ARTIFACTS_DIR", str(tmp_path))
    with pytest.raises(ConfigError) as error:
        create_app("test")
    message = str(error.value)
    assert "CLASSIFIER_BACKEND=trained" in message
    assert "intelligence_centers.joblib" in message
    assert "no se usa el stub" in message


def test_trained_does_not_start_even_with_artifacts_until_features_are_defined(monkeypatch, tmp_path):
    for system in TAXONOMIES:
        (tmp_path / f"{system}.joblib").write_bytes(b"")
    monkeypatch.setenv("CLASSIFIER_BACKEND", "trained")
    monkeypatch.setenv("CLASSIFIER_ARTIFACTS_DIR", str(tmp_path))
    with pytest.raises(ConfigError, match="codificación"):
        create_app("test")


# --- the registry -------------------------------------------------------------------------------


def test_an_unknown_backend_stops_the_app_by_name(monkeypatch):
    monkeypatch.setenv("CLASSIFIER_BACKEND", "random_forest")
    with pytest.raises(ConfigError, match="CLASSIFIER_BACKEND desconocido: 'random_forest'"):
        create_app("test")


def test_production_requires_choosing_a_backend(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@host/db")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://nureon.example")
    monkeypatch.setenv("COGNITO_USER_POOL_ID", "pool")
    monkeypatch.setenv("COGNITO_APP_CLIENT_ID", "client")
    monkeypatch.setenv("IDENTITY_PROVIDER", "cognito")
    monkeypatch.delenv("CLASSIFIER_BACKEND")
    with pytest.raises(ConfigError, match="CLASSIFIER_BACKEND"):
        get_config("production")


def test_built_in_names_cannot_be_replaced():
    with pytest.raises(ValueError):
        registry.register("stub", lambda config: StubClassifier())


# --- the seam refuses what does not fit it -----------------------------------------------------


def _valid() -> Classification:
    return from_distributions(tally_distributions(answers_for_groups(TYPE_TABLE[2])), "x-1")


@pytest.mark.parametrize(
    "broken",
    [
        lambda c: replace(c, eneatype=10),
        lambda c: replace(c, confidence_margin=-0.1),
        lambda c: replace(c, model_version=""),
        lambda c: replace(c, systems={k: v for k, v in c.systems.items() if k != "harmonic"}),
        lambda c: replace(
            c, systems={**c.systems, "harmonic": SystemPrediction("harmonic", "gut", c.systems["harmonic"].probabilities)}
        ),
        lambda c: replace(
            c, systems={**c.systems, "hornevian": SystemPrediction("hornevian", "assertive", {"assertive": 1.0})}
        ),
        lambda c: replace(
            c,
            systems={
                **c.systems,
                "hornevian": SystemPrediction("hornevian", "assertive", {"assertive": 0.9, "compliant": 0.9, "withdrawn": 0}),
            },
        ),
        lambda c: "not a classification",
    ],
)
def test_validate_refuses_an_output_that_does_not_fit(broken):
    with pytest.raises(InvalidClassification):
        validate(broken(_valid()))
