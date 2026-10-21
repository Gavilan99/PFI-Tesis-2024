"""The cut plan and the trained models at startup: what loads, and every way the app refuses to start.

The session's synthetic artifacts (tests/conftest.py) are copied into a temporary folder and broken one
way at a time. Nothing here touches app/ml/artifacts/.
"""

import json
import os
import shutil
from pathlib import Path

import joblib
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app import create_app
from app.config import ConfigError
from app.ml.config import TAXONOMIES
from app.ml.cut_plan import CUT_SIZES, DEFAULT_ARTIFACTS_DIR, artifacts_dir, load_cut_plan
from app.ml.trained import TrainedClassifier


@pytest.fixture()
def artifacts(tmp_path, monkeypatch) -> Path:
    """A private copy of the session's synthetic artifacts, which the app is pointed at."""
    copy = tmp_path / "artifacts"
    shutil.copytree(os.environ["CLASSIFIER_ARTIFACTS_DIR"], copy)
    monkeypatch.setenv("CLASSIFIER_ARTIFACTS_DIR", str(copy))
    return copy


def _edit(path: Path, change) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(json.dumps(data), encoding="utf-8")


class _Config:
    def __init__(self, directory):
        self.CLASSIFIER_ARTIFACTS_DIR = directory


# --- the plan -----------------------------------------------------------------------------------


def test_the_plan_has_three_nested_cuts_of_40_90_145(app):
    plan = app.extensions["cut_plan"]
    assert [cut.size for cut in plan.cuts] == list(CUT_SIZES) == [40, 90, 145]
    assert [cut.number for cut in plan.cuts] == [1, 2, 3]
    assert [len(cut.serve_new_items) for cut in plan.cuts] == [40, 50, 55]
    served = []
    for cut in plan.cuts:
        served += cut.serve_new_items
        assert set(served) == set(cut.model_items)
    assert all(0 <= cut.estimated_accuracy <= 1 for cut in plan.cuts)
    assert plan.synthetic


def test_the_plan_is_read_from_the_configured_folder_with_app_ml_artifacts_by_default():
    assert artifacts_dir(_Config(None)) == DEFAULT_ARTIFACTS_DIR
    assert DEFAULT_ARTIFACTS_DIR.parts[-3:] == ("app", "ml", "artifacts")
    assert artifacts_dir(_Config("C:/x")) == Path("C:/x")


def test_the_stub_needs_the_plan_too(artifacts):
    (artifacts / "manifest.json").unlink()
    with pytest.raises(ConfigError, match="manifest.json"):
        create_app("test")


def test_cuts_that_are_not_nested_stop_the_app(artifacts):
    def unnest(manifest):
        cut2 = manifest["cuts"][1]
        dropped = manifest["cuts"][0]["model_items"][0]
        outsider = next(c for c in manifest["cuts"][2]["model_items"] if c not in cut2["model_items"])
        cut2["model_items"] = [outsider if c == dropped else c for c in cut2["model_items"]]

    _edit(artifacts / "manifest.json", unnest)
    with pytest.raises(ConfigError, match="no está anidado") as error:
        create_app("test")
    assert "corte 2 (90)" in str(error.value)
    assert "la app no arranca" in str(error.value)


def test_sizes_other_than_40_90_145_stop_the_app(artifacts):
    _edit(artifacts / "manifest.json", lambda m: m["cuts"][0].update(size=20))
    with pytest.raises(ConfigError, match=r"tienen que ser \[40, 90, 145\]"):
        create_app("test")


def test_serve_new_items_must_cover_exactly_what_the_cut_adds(artifacts):
    def drop_one(manifest):
        manifest["cuts"][1]["serve_new_items"] = manifest["cuts"][1]["serve_new_items"][:-1]

    _edit(artifacts / "manifest.json", drop_one)
    with pytest.raises(ConfigError, match="serve_new_items no cubre exactamente"):
        create_app("test")


def test_serve_new_items_must_not_repeat_an_earlier_item(artifacts):
    def repeat(manifest):
        new = manifest["cuts"][1]["serve_new_items"]
        new[0] = manifest["cuts"][0]["serve_new_items"][0]

    _edit(artifacts / "manifest.json", repeat)
    with pytest.raises(ConfigError, match="serve_new_items no cubre exactamente"):
        create_app("test")


def test_every_cut_needs_its_estimated_accuracy(artifacts):
    _edit(artifacts / "precision_by_items.json", lambda p: p["cuts"].pop())
    with pytest.raises(ConfigError, match=r"corte 3 \(145\): precision_by_items.json"):
        create_app("test")


def test_an_accuracy_outside_0_1_stops_the_app(artifacts):
    _edit(artifacts / "precision_by_items.json", lambda p: p["cuts"][0].update(estimated_type_accuracy=1.7))
    with pytest.raises(ConfigError, match="precisión estimada entre 0 y 1"):
        load_cut_plan(_Config(artifacts))


# --- synthetic artifacts in production ----------------------------------------------------------


def _production_env(monkeypatch, backend: str) -> None:
    for name, value in {
        "SECRET_KEY": "x", "DATABASE_URL": "postgresql+psycopg://u:p@host/db",
        "CORS_ALLOWED_ORIGINS": "https://nureon.example", "IDENTITY_PROVIDER": "cognito",
        "COGNITO_USER_POOL_ID": "us-east-2_pool", "COGNITO_APP_CLIENT_ID": "client",
        "MAIL_SENDER": "ses", "CONTACT_MAIL_TO": "contacto@example.invalid", "CLASSIFIER_BACKEND": backend,
        "CONSENT_VERSION": "2026-10-20",
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("AWS_PROFILE", raising=False)


@pytest.mark.parametrize("backend", ["stub", "trained"])
def test_production_refuses_synthetic_artifacts(artifacts, monkeypatch, backend):
    _production_env(monkeypatch, backend)
    with pytest.raises(ConfigError, match="sintéticos") as error:
        create_app("production")
    assert "En producción la app no arranca con ellos" in str(error.value)


# --- the trained models at startup --------------------------------------------------------------


def _trained(monkeypatch):
    monkeypatch.setenv("CLASSIFIER_BACKEND", "trained")
    return create_app("test")


def test_trained_loads_the_twelve_models_and_never_the_stub(artifacts, monkeypatch, app):
    other = _trained(monkeypatch)
    try:
        classifier = other.extensions["classifier"]
        assert isinstance(classifier, TrainedClassifier)
        assert sorted(classifier.models) == [1, 2, 3]
        assert all(sorted(models) == sorted(TAXONOMIES) for models in classifier.models.values())
        assert classifier.model_version.startswith("synthetic-")
    finally:
        other.extensions["sqlalchemy_engine"].dispose()
        from app.extensions import session_factory
        session_factory.configure(bind=app.extensions["sqlalchemy_engine"])


def test_a_missing_joblib_stops_the_app_and_names_it(artifacts, monkeypatch):
    (artifacts / "cut_090" / "harmonic.joblib").unlink()
    with pytest.raises(ConfigError) as error:
        _trained(monkeypatch)
    message = str(error.value)
    assert "falta cut_090/harmonic.joblib" in message
    assert "no se usa el stub" in message


def test_another_scikit_learn_version_stops_the_app(artifacts, monkeypatch):
    _edit(artifacts / "manifest.json", lambda m: m.update(sklearn="0.0.1"))
    with pytest.raises(ConfigError, match=r"scikit-learn instalado .*, el manifest pide 0.0.1"):
        _trained(monkeypatch)


def test_another_numpy_version_stops_the_app(artifacts, monkeypatch):
    _edit(artifacts / "manifest.json", lambda m: m.update(numpy="0.0.1"))
    with pytest.raises(ConfigError, match=r"numpy instalado .*, el manifest pide 0.0.1"):
        _trained(monkeypatch)


def test_a_bare_forest_is_not_a_pipeline_and_stops_the_app(artifacts, monkeypatch):
    path = artifacts / "cut_040" / "hornevian.joblib"
    joblib.dump(joblib.load(path).named_steps["rf"], path)
    with pytest.raises(ConfigError, match="cut_040/hornevian.joblib no es un Pipeline con un solo paso 'rf'"):
        _trained(monkeypatch)


def test_a_pipeline_with_another_step_stops_the_app(artifacts, monkeypatch):
    path = artifacts / "cut_040" / "hornevian.joblib"
    joblib.dump(Pipeline([("scale", StandardScaler()), ("rf", joblib.load(path).named_steps["rf"])]), path)
    with pytest.raises(ConfigError, match="no es un Pipeline con un solo paso 'rf'"):
        _trained(monkeypatch)


def test_classes_of_another_system_stop_the_app(artifacts, monkeypatch):
    # The harmonic model saved where the hornevian one goes: right shape, wrong groups.
    shutil.copy(artifacts / "cut_040" / "harmonic.joblib", artifacts / "cut_040" / "hornevian.joblib")
    with pytest.raises(ConfigError, match=r"cut_040/hornevian.joblib: classes_ .* no son los tres grupos de hornevian"):
        _trained(monkeypatch)


def test_a_model_with_two_classes_stops_the_app(artifacts, monkeypatch):
    columns = len(json.loads((artifacts / "manifest.json").read_text(encoding="utf-8"))["cuts"][0]["columns"])
    forest = RandomForestClassifier(n_estimators=2).fit([[0] * columns, [1] * columns], ["gut", "heart"])
    joblib.dump(Pipeline([("rf", forest)]), artifacts / "cut_040" / "intelligence_centers.joblib")
    with pytest.raises(ConfigError, match="no son los tres grupos de intelligence_centers"):
        _trained(monkeypatch)


def test_a_model_of_another_cut_stops_the_app(artifacts, monkeypatch):
    shutil.copy(artifacts / "cut_090" / "object_relations.joblib", artifacts / "cut_040" / "object_relations.joblib")
    with pytest.raises(ConfigError, match=r"cut_040/object_relations.joblib: n_features_in_ 210 no coincide con las 96"):
        _trained(monkeypatch)
