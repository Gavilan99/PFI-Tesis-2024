import uuid
from contextlib import contextmanager

from app import create_app
from app.db.models import AnswerOption, Question
from app.db.models.enums import QuestionType
from app.extensions import session_factory
from app.ml.classification import Answer
from app.ml.config import TAXONOMIES, TYPE_TABLE
from app.services.question_bank import load_bank
from scripts.seed_filler_bank import FILLER_VERSION, build_filler_bank
from tests.attempt_helpers import answer_body, questions, start
from tests.db_helpers import bound_session


@contextmanager
def app_with_backend(main_app, monkeypatch, backend: str):
    """A second app built with `CLASSIFIER_BACKEND=backend`, exactly as a deployment would build it,
    with its own rolled-back session and the filler bank loaded.

    Building an app points the shared session factory at its engine, so a test using this must not
    also use `db_session`/`api` of the main app. The main app's engine is restored afterwards.
    """
    monkeypatch.setenv("CLASSIFIER_BACKEND", backend)
    other = create_app("test")
    try:
        with bound_session(other) as session:
            load_bank(session, build_filler_bank(), version=FILLER_VERSION, activate=True)
            session.commit()
            yield other, session
    finally:
        session_factory.configure(bind=main_app.extensions["sqlalchemy_engine"])
        other.extensions["sqlalchemy_engine"].dispose()


def scenario(system: str, group: str) -> Answer:
    return Answer(
        question_id=uuid.uuid4(),
        option_id=uuid.uuid4(),
        grouping_system=system,
        question_type=QuestionType.SCENARIO,
        group_label=group,
        option_position=1,
        option_count=3,
    )


def likert(system: str, group: str, position: int) -> Answer:
    return Answer(
        question_id=uuid.uuid4(),
        option_id=uuid.uuid4(),
        grouping_system=system,
        question_type=QuestionType.MULTIPLE_CHOICE,
        group_label=group,
        option_position=position,
        option_count=5,
    )


def answers_for_groups(groups: dict[str, str]) -> list[Answer]:
    """One scenario answer per system, for the given group."""
    return [scenario(system, groups[system]) for system in TAXONOMIES]


def choose_for_type(session, item: dict, eneatype: int) -> str:
    """The option of a served item that points at `eneatype`: in a scenario item, the option of the
    type's group; in a Likert item, full agreement if it targets the type's group, else none."""
    option_ids = [uuid.UUID(o["id"]) for o in item["answerOptions"]]
    question = session.get(Question, uuid.UUID(item["id"]))
    wanted = TYPE_TABLE[eneatype][question.grouping_system.value]
    groups = {o.id: o.group_label for o in session.query(AnswerOption).filter(AnswerOption.id.in_(option_ids))}
    if question.question_type is QuestionType.SCENARIO:
        return next(str(i) for i in option_ids if groups[i] == wanted)
    position = len(option_ids) if groups[option_ids[0]] == wanted else 1
    return item["answerOptions"][position - 1]["id"]


def complete_as_type(client, headers, session, eneatype: int) -> dict:
    """Start an attempt, answer every item towards `eneatype`, close it. Returns the attempt."""
    attempt = start(client, headers)
    for item in questions(client, headers, attempt["id"]):
        body = answer_body(item["id"], choose_for_type(session, item, eneatype))
        response = client.post(f"/api/attempts/{attempt['id']}/responses", headers=headers, json=body)
        assert response.status_code == 200, response.get_json()
    response = client.post(f"/api/attempts/{attempt['id']}/complete", headers=headers)
    assert response.status_code == 200, response.get_json()
    return attempt
