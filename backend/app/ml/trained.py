"""`CLASSIFIER_BACKEND=trained`: the twelve Random Forests of the fixed item cuts, four per cut.

Contract with the training: `app/ml/training/README.md`. At startup the twelve models of the cut
plan (`app.ml.cut_plan`) are loaded and checked; the app refuses to start, and says why, if:
- the installed scikit-learn or numpy is not the version in the manifest;
- a file is missing, or is not a `Pipeline` whose only step is `rf`;
- a model's `classes_` are not the three canonical groups of its system;
- a model's `n_features_in_` is not the number of columns of its cut.
It never falls back to the stub: a stub result presented as the model's would be the worst error.

Classifying an attempt:
1. `{code: option_position}` from its answers (the code is rebuilt from `questions.display_order`);
2. the cut whose `model_items` are exactly what was answered; no match is an error, never a default;
3. `app.ml.training.encoding.encode_one`, checking the columns against the manifest's;
4. `predict_proba` of the cut's four pipelines, and the four distributions to `from_distributions`.
The model version stored is the manifest's plus the cut: `<version>/cut_040`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.config import ConfigError
from app.db.models.enums import QuestionType
from app.ml.classification import Answer, Classification, from_distributions
from app.ml.config import TAXONOMIES
from app.ml.cut_plan import Cut, CutPlan, load_cut_plan, question_code

MODEL_VERSION_LIMIT = 64


def cut_model_version(plan: CutPlan, cut: Cut) -> str:
    return f"{plan.model_version}/{cut.directory}"


class TrainedClassifier:
    def __init__(self, plan: CutPlan, models: Mapping[int, Mapping[str, object]]):
        self.plan = plan
        self.models = models
        self.model_version = plan.model_version

    def classify(self, answers: Sequence[Answer]) -> Classification:
        # Imported here: the stub path never loads scikit-learn, and this module is imported lazily too.
        import numpy as np

        from app.ml.training.bank import LIKERT, SCENARIO, Item
        from app.ml.training.encoding import columns, encode_one

        by_code = {question_code(answer.question_order): answer for answer in answers}
        if len(by_code) != len(answers):
            raise ValueError("two answers share a question number")
        cut = next((c for c in self.plan.cuts if set(c.model_items) == set(by_code)), None)
        if cut is None:
            raise ValueError(f"{len(by_code)} answered items match no cut of the plan exactly")

        items = []
        for code in cut.model_items:
            answer = by_code[code]
            fmt = SCENARIO if answer.question_type is QuestionType.SCENARIO else LIKERT
            items.append(Item(code=code, order=answer.question_order, system=answer.grouping_system,
                              fmt=fmt, n_options=answer.option_count))
        if tuple(columns(items)) != cut.columns:
            raise ValueError(f"the attempt's items do not encode to the columns of {cut.directory}")
        row = np.asarray([encode_one({code: by_code[code].option_position for code in cut.model_items}, items)])

        distributions = {}
        for system, model in self.models[cut.number].items():
            probabilities = dict(zip(model.classes_, model.predict_proba(row)[0]))
            distributions[system] = {group: float(probabilities[group]) for group in TAXONOMIES[system]}
        return from_distributions(distributions, cut_model_version(self.plan, cut))


def build_trained(config) -> TrainedClassifier:
    import joblib
    import numpy
    import sklearn
    from sklearn.pipeline import Pipeline

    plan = load_cut_plan(config)
    problems: list[str] = []
    if sklearn.__version__ != plan.sklearn_version:
        problems.append(f"scikit-learn instalado {sklearn.__version__}, el manifest pide {plan.sklearn_version}")
    if numpy.__version__ != plan.numpy_version:
        problems.append(f"numpy instalado {numpy.__version__}, el manifest pide {plan.numpy_version}")
    longest = max(len(cut_model_version(plan, cut)) for cut in plan.cuts)
    if longest > MODEL_VERSION_LIMIT:
        problems.append(f"model_version más el corte ocupa {longest} caracteres; la columna admite "
                        f"{MODEL_VERSION_LIMIT}")
    if problems:
        _refuse(plan, problems)

    models: dict[int, dict[str, object]] = {}
    for cut in plan.cuts:
        models[cut.number] = {}
        for system, groups in TAXONOMIES.items():
            path = plan.directory / cut.directory / f"{system}.joblib"
            where = f"{cut.directory}/{path.name}"
            if not path.is_file():
                problems.append(f"falta {where}")
                continue
            try:
                model = joblib.load(path)
            except Exception as error:  # a corrupt or foreign pickle: refuse, naming it
                problems.append(f"{where} no se pudo cargar ({type(error).__name__})")
                continue
            if not isinstance(model, Pipeline) or list(model.named_steps) != ["rf"]:
                problems.append(f"{where} no es un Pipeline con un solo paso 'rf'")
                continue
            classes = [str(c) for c in model.classes_]
            if len(classes) != len(groups) or set(classes) != set(groups):
                problems.append(f"{where}: classes_ {classes} no son los tres grupos de {system}")
            if getattr(model, "n_features_in_", None) != len(cut.columns):
                problems.append(f"{where}: n_features_in_ {getattr(model, 'n_features_in_', None)} no "
                                f"coincide con las {len(cut.columns)} columnas del corte")
            models[cut.number][system] = model
    if problems:
        _refuse(plan, problems)
    return TrainedClassifier(plan, models)


def _refuse(plan: CutPlan, problems: list[str]):
    raise ConfigError(
        f"CLASSIFIER_BACKEND=trained no puede cargar los modelos de {plan.directory}; la app no arranca "
        "(no se usa el stub en su lugar):\n  - " + "\n  - ".join(problems)
    )
