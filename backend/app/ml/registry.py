"""Which classifier backend runs: `CLASSIFIER_BACKEND`, read once when the app is created.

Each backend is a factory `config -> Classifier`, imported lazily, so the stub path never loads
scikit-learn. Switching backends is changing the variable and restarting; no route or service
changes. A new implementation (a test double, the trained models) enters with `register`.
"""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module

from app.config import ConfigError
from app.ml.classification import Classifier

ClassifierFactory = Callable[[object], Classifier]

DEFAULT_BACKEND = "stub"

# Built-in backends, as "module:factory", imported only when chosen.
_BUILT_IN: dict[str, str] = {
    "stub": "app.ml.stub:build_stub",
    "legacy_tree": "app.ml.legacy.tree:build_legacy_tree",
    "trained": "app.ml.trained:build_trained",
}
_registered: dict[str, ClassifierFactory] = {}


def register(name: str, factory: ClassifierFactory) -> None:
    if name in _BUILT_IN:
        raise ValueError(f"'{name}' is a built-in classifier backend")
    _registered[name] = factory


def unregister(name: str) -> None:
    _registered.pop(name, None)


def backend_names() -> list[str]:
    return [*_BUILT_IN, *_registered]


def build_classifier(config) -> Classifier:
    name = config.CLASSIFIER_BACKEND
    if name in _BUILT_IN:
        module, _, attribute = _BUILT_IN[name].partition(":")
        factory = getattr(import_module(module), attribute)
    elif name in _registered:
        factory = _registered[name]
    else:
        valid = ", ".join(backend_names())
        raise ConfigError(f"CLASSIFIER_BACKEND desconocido: '{name}'. Opciones válidas: {valid}")
    return factory(config)
