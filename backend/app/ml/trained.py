"""`CLASSIFIER_BACKEND=trained`: the four Random Forests of the ML design. They do not exist yet.

Without the four trained artifacts the app refuses to start, and says so. It never falls back to the
stub: a stub result presented as the model's would be the worst possible error.

When they exist, this backend runs one `app.ml.classifiers.TaxonomyClassifier` per grouping system
and hands the four distributions to `app.ml.classification.from_distributions`: the same
intersection layer the stub uses. What is still undecided is how an attempt's answers become each
classifier's features (it depends on the real bank and on the open `NO_PREGUNTADO` proposal of the
ML design), so even with artifacts present this backend refuses to start until that is defined.
"""

from __future__ import annotations

from pathlib import Path

from app.config import ConfigError
from app.ml.config import TAXONOMIES

DEFAULT_ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


def artifact_paths(directory: Path) -> dict[str, Path]:
    return {system: directory / f"{system}.joblib" for system in TAXONOMIES}


def build_trained(config) -> None:
    directory = Path(getattr(config, "CLASSIFIER_ARTIFACTS_DIR", None) or DEFAULT_ARTIFACTS_DIR)
    missing = [path.name for path in artifact_paths(directory).values() if not path.is_file()]
    if missing:
        raise ConfigError(
            "CLASSIFIER_BACKEND=trained necesita los cuatro clasificadores entrenados y no están: "
            f"faltan {', '.join(missing)} en {directory}. La app no arranca: no se usa el stub en su "
            "lugar. Para correr sin modelo entrenado, elegí CLASSIFIER_BACKEND=stub o legacy_tree."
        )
    raise ConfigError(
        "CLASSIFIER_BACKEND=trained: los artefactos están, pero la codificación de las respuestas a "
        "features todavía no está definida (depende del banco real). La app no arranca."
    )
