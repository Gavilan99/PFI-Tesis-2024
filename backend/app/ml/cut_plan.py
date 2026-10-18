"""The plan of fixed item cuts: which items each cut serves, in what order, and how accurate it is.

Decision of 17/10 (PDR "Product Classifier and Fixed Item Cuts"): the test is served in three fixed,
nested cuts of 40, 90 and 145 items. Everyone gets the same items in the same order. After each cut
the person sees the estimated accuracy of the cut just finished and of the next one.

The plan is read from the artifacts the training writes (`app/ml/training/README.md`):
- `manifest.json` -> `cuts[i]`: `size`, `directory`, `model_items` (column order), `columns` and
  `serve_new_items` (what the cut adds, in serving order);
- `precision_by_items.json` -> `cuts[i].estimated_type_accuracy`, the number the product shows.

It does not depend on the classifier: the stub serves by these cuts too. It is read and validated once,
when the app is created, from `CLASSIFIER_ARTIFACTS_DIR` (by default `app/ml/artifacts/`). If anything
is off, the app does not start.

An item is its bank code (`Q007`); its number is `questions.display_order` in the active version (see
scripts/import_question_bank.py), which is how attempts resolve it.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.config import ConfigError

DEFAULT_ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
CUT_SIZES = (40, 90, 145)
SYNTHETIC_PREFIX = "synthetic-"
_CODE = re.compile(r"Q([0-9]{3})")
_COLUMN = re.compile(r"(Q[0-9]{3})(?:_o([0-9]))?")


@dataclass(frozen=True)
class Cut:
    number: int                         # 1-based
    size: int
    directory: str
    model_items: tuple[str, ...]        # bank codes, in the models' column order
    columns: tuple[str, ...]
    serve_new_items: tuple[str, ...]    # the codes this cut adds, in serving order
    estimated_accuracy: float           # estimated eneatype accuracy, 0-1

    @property
    def new_item_orders(self) -> tuple[int, ...]:
        return tuple(question_order(code) for code in self.serve_new_items)


@dataclass(frozen=True)
class CutPlan:
    directory: Path
    model_version: str
    sklearn_version: str
    numpy_version: str
    cuts: tuple[Cut, ...]

    @property
    def synthetic(self) -> bool:
        return self.model_version.startswith(SYNTHETIC_PREFIX)

    def cut_by_size(self, size: int) -> Cut | None:
        return next((cut for cut in self.cuts if cut.size == size), None)

    def next_cut(self, cut: Cut) -> Cut | None:
        return self.cuts[cut.number] if cut.number < len(self.cuts) else None


def question_order(code: str) -> int:
    """`Q007` -> 7: the item's `questions.display_order`."""
    match = _CODE.fullmatch(code)
    if not match:
        raise ValueError(f"'{code}' is not a bank code (Q + three digits)")
    return int(match.group(1))


def question_code(order: int) -> str:
    return f"Q{order:03d}"


def artifacts_dir(config) -> Path:
    return Path(getattr(config, "CLASSIFIER_ARTIFACTS_DIR", None) or DEFAULT_ARTIFACTS_DIR)


def load_cut_plan(config) -> CutPlan:
    directory = artifacts_dir(config)
    manifest = _read_json(directory / "manifest.json")
    precision = _read_json(directory / "precision_by_items.json")
    problems: list[str] = []

    version = manifest.get("model_version")
    if not isinstance(version, str) or not version:
        problems.append("manifest.json no tiene model_version")
        version = ""
    raw_cuts = manifest.get("cuts")
    if not isinstance(raw_cuts, list) or not raw_cuts:
        _fail(directory, ["manifest.json no tiene cortes (cuts)"])

    sizes = [c.get("size") for c in raw_cuts]
    if sizes != list(CUT_SIZES):
        problems.append(f"los tamaños de los cortes son {sizes}, tienen que ser {list(CUT_SIZES)}")

    accuracies = {c.get("size"): c.get("estimated_type_accuracy") for c in precision.get("cuts") or []}
    cuts: list[Cut] = []
    previous: set[str] = set()
    for number, raw in enumerate(raw_cuts, start=1):
        size = raw.get("size")
        where = f"corte {number} ({size})"
        model_items = list(raw.get("model_items") or [])
        serve_new = list(raw.get("serve_new_items") or [])
        columns = list(raw.get("columns") or [])
        bad = [code for code in model_items + serve_new if not _CODE.fullmatch(str(code))]
        if bad:
            problems.append(f"{where}: códigos que no son Q + tres dígitos: {bad[:5]}")
        if len(set(model_items)) != len(model_items) or len(model_items) != size:
            problems.append(f"{where}: model_items tiene {len(model_items)} códigos distintos o repetidos, "
                            f"tienen que ser {size} distintos")
        if not previous <= set(model_items):
            problems.append(f"{where}: no está anidado: le faltan ítems del corte anterior "
                            f"({sorted(previous - set(model_items))[:5]})")
        added = set(model_items) - previous
        if len(serve_new) != len(set(serve_new)) or set(serve_new) != added:
            problems.append(f"{where}: serve_new_items no cubre exactamente lo que agrega el corte "
                            f"({len(serve_new)} códigos servidos, {len(added)} agregados)")
        column_items = []
        for column in columns:
            match = _COLUMN.fullmatch(str(column))
            if not match:
                problems.append(f"{where}: columna desconocida {column!r}")
                break
            if match.group(1) not in column_items:
                column_items.append(match.group(1))
        if column_items != model_items:
            problems.append(f"{where}: las columnas no siguen el orden de model_items")
        accuracy = accuracies.get(size)
        if not isinstance(accuracy, (int, float)) or isinstance(accuracy, bool) or not 0 <= accuracy <= 1:
            problems.append(f"{where}: precision_by_items.json no tiene una precisión estimada entre 0 y 1")
            accuracy = 0.0
        if not raw.get("directory"):
            problems.append(f"{where}: falta directory")
        cuts.append(Cut(number=number, size=size, directory=str(raw.get("directory") or ""),
                        model_items=tuple(model_items), columns=tuple(columns),
                        serve_new_items=tuple(serve_new), estimated_accuracy=float(accuracy)))
        previous = set(model_items)

    if problems:
        _fail(directory, problems)
    return CutPlan(directory=directory, model_version=version, sklearn_version=str(manifest.get("sklearn")),
                   numpy_version=str(manifest.get("numpy")), cuts=tuple(cuts))


def _read_json(path: Path) -> dict:
    if not path.is_file():
        raise ConfigError(
            f"Falta {path.name} en {path.parent}: sin el plan de cortes la app no arranca. Generá "
            "artefactos sintéticos para desarrollo con scripts/make_dev_artifacts.py --out <carpeta> y "
            "apuntá CLASSIFIER_ARTIFACTS_DIR ahí."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ConfigError(f"No se pudo leer {path}: {error}. La app no arranca.") from None
    if not isinstance(data, dict):
        raise ConfigError(f"{path} no es un objeto JSON. La app no arranca.")
    return data


def _fail(directory: Path, problems: list[str]):
    raise ConfigError(
        f"El plan de cortes de {directory} no es válido; la app no arranca:\n  - " + "\n  - ".join(problems)
    )
