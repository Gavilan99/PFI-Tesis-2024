import csv
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import select, text

from app.db.models import AnswerOption, Question, Response, TestAttempt, User
from app.db.models.enums import AttemptTier, GroupingSystem, QuestionType
from app.repositories import question_repository
from app.services.question_bank import QuestionBankError, load_bank, validate_bank
from scripts import import_question_bank
from scripts.import_question_bank import CsvFormatError, read_bank_csv
from tests.db_helpers import option_ids

FIXTURE = Path(__file__).parent / "fixtures" / "question_bank_filler.csv"


def read_rows(path: Path = FIXTURE) -> tuple[list[str], list[dict]]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames), list(reader)


def write_csv(tmp_path: Path, headers: list[str], rows: list[dict]) -> Path:
    path = tmp_path / "bank.csv"
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    return path


def problems_for(tmp_path: Path, mutate) -> list[str]:
    """Problems reported for the fixture after `mutate(rows)` edits it, from parse or validation."""
    headers, rows = read_rows()
    mutate(rows)
    try:
        return validate_bank(read_bank_csv(write_csv(tmp_path, headers, rows)))
    except CsvFormatError as error:
        return error.problems


# --- parsing ------------------------------------------------------------------------------------


def test_fixture_is_read_with_its_bom_and_translated_to_the_canonical_vocabulary():
    assert FIXTURE.read_bytes().startswith(b"\xef\xbb\xbf")
    bank = read_bank_csv(FIXTURE)

    assert len(bank) == 8
    assert validate_bank(bank) == []
    assert {q.grouping_system for q in bank} == set(GroupingSystem)
    assert {q.question_type for q in bank} == {QuestionType.SCENARIO, QuestionType.MULTIPLE_CHOICE}
    first = bank[0]
    assert first.source_id == "T01"
    assert [o.group_label for o in first.options] == ["heart", "head", "gut"]
    assert "ítem" in first.prompt_text


def test_missing_headers_are_named_before_any_row_is_read(tmp_path):
    headers, rows = read_rows()
    renamed = ["grupo" if h == "group_label" else h for h in headers]
    rows = [{("grupo" if k == "group_label" else k): v for k, v in row.items()} for row in rows]
    with pytest.raises(CsvFormatError) as excinfo:
        read_bank_csv(write_csv(tmp_path, renamed, rows))
    message = str(excinfo.value)
    assert "Faltan columnas en el CSV: group_label." in message
    assert "grupo" in message
    assert "COLUMNS" in message


def test_unknown_system_label_stops_the_load(tmp_path):
    def mutate(rows):
        rows[0]["grouping_system"] = "Centros"

    assert "Línea 2: sistema desconocido 'Centros'." in problems_for(tmp_path, mutate)


def test_unknown_group_label_stops_the_load(tmp_path):
    def mutate(rows):
        rows[0]["group_label"] = "Instinto"

    assert "Línea 2: grupo desconocido 'Instinto'." in problems_for(tmp_path, mutate)


def test_labels_are_not_matched_without_their_accents(tmp_path):
    def mutate(rows):
        rows[0]["group_label"] = "Corazon"

    assert "Línea 2: grupo desconocido 'Corazon'." in problems_for(tmp_path, mutate)


def test_labels_match_regardless_of_case_and_spaces(tmp_path):
    def mutate(rows):
        rows[0]["group_label"] = "  corazón "
        rows[0]["grouping_system"] = "CENTROS DE INTELIGENCIA"

    assert problems_for(tmp_path, mutate) == []


def test_group_from_another_system_stops_the_load(tmp_path):
    def mutate(rows):
        rows[0]["group_label"] = "Asertiva"

    problems = problems_for(tmp_path, mutate)
    assert any("assertive no pertenecen al sistema intelligence_centers" in p for p in problems)


def test_scenario_item_repeating_a_group_stops_the_load(tmp_path):
    def mutate(rows):
        rows[1]["group_label"] = rows[0]["group_label"]

    problems = problems_for(tmp_path, mutate)
    assert any("Pregunta T01: un ítem de escenario" in p for p in problems)


def test_scenario_item_with_two_options_stops_the_load(tmp_path):
    def mutate(rows):
        del rows[2]

    problems = problems_for(tmp_path, mutate)
    assert any("Pregunta T01: un ítem de escenario" in p for p in problems)


def test_likert_item_without_five_options_stops_the_load(tmp_path):
    def mutate(rows):
        del rows[7]  # one of T02's five options

    assert "Pregunta T02: un ítem Likert tiene que tener 5 opciones; tiene 4." in problems_for(
        tmp_path, mutate
    )


def test_likert_item_mixing_groups_stops_the_load(tmp_path):
    def mutate(rows):
        rows[4]["group_label"] = "Mente"

    problems = problems_for(tmp_path, mutate)
    assert any("Pregunta T02: las opciones de un ítem Likert" in p for p in problems)


def test_out_of_scope_question_type_stops_the_load(tmp_path):
    def mutate(rows):
        for row in rows:
            if row["question_id"] == "T01":
                row["question_type"] = "ordering"

    assert "Línea 2: tipo de pregunta desconocido 'ordering'." in problems_for(tmp_path, mutate)


def test_main_reports_a_broken_header_and_exits_nonzero(tmp_path, capsys):
    headers, rows = read_rows()
    broken = ["prompt" if h == "prompt_text" else h for h in headers]
    rows = [{("prompt" if k == "prompt_text" else k): v for k, v in row.items()} for row in rows]
    path = write_csv(tmp_path, broken, rows)

    code = import_question_bank.main(["--csv", str(path), "--version", "1", "--dry-run"])

    assert code == 1
    assert "Faltan columnas en el CSV: prompt_text." in capsys.readouterr().err


def test_main_refuses_version_zero(capsys):
    assert import_question_bank.main(["--csv", str(FIXTURE), "--version", "0", "--dry-run"]) == 1
    assert "reservada para el relleno" in capsys.readouterr().err


# --- loading ------------------------------------------------------------------------------------


def test_load_inserts_the_bank(db_session):
    summary = load_bank(db_session, read_bank_csv(FIXTURE), version=1, activate=False)

    assert (summary.inserted, summary.updated, summary.unchanged, summary.removed) == (8, 0, 0, 0)
    assert summary.counts["questions"] == 8
    assert summary.counts["options"] == 4 * 3 + 4 * 5
    assert summary.counts["questions_by_type"] == {"scenario": 4, "multiple_choice": 4}
    assert summary.active_versions == []


def test_reimporting_the_same_version_does_not_duplicate(db_session):
    bank = read_bank_csv(FIXTURE)
    load_bank(db_session, bank, version=1, activate=False)
    summary = load_bank(db_session, bank, version=1, activate=False)

    assert (summary.inserted, summary.updated, summary.unchanged, summary.removed) == (0, 0, 8, 0)
    assert db_session.query(Question).filter_by(version=1).count() == 8
    assert db_session.query(AnswerOption).join(Question).filter(Question.version == 1).count() == 32


def test_activating_a_version_deactivates_the_previous_one(db_session):
    bank = read_bank_csv(FIXTURE)
    load_bank(db_session, bank, version=1, activate=True)
    assert question_repository.active_versions(db_session) == [1]

    summary = load_bank(db_session, bank, version=2, activate=True)

    assert summary.active_versions == [2]
    assert db_session.query(Question).filter_by(version=1, is_active=True).count() == 0
    assert db_session.query(Question).filter_by(version=2, is_active=True).count() == 8


def test_changed_question_without_responses_is_updated(db_session, tmp_path):
    load_bank(db_session, read_bank_csv(FIXTURE), version=1, activate=False)
    headers, rows = read_rows()
    for row in rows:
        if row["question_id"] == "T01":
            row["prompt_text"] = "Enunciado de prueba 1, corregido (relleno de test)."

    summary = load_bank(
        db_session, read_bank_csv(write_csv(tmp_path, headers, rows)), version=1, activate=False
    )

    assert (summary.updated, summary.unchanged) == (1, 7)
    question = db_session.scalars(select(Question).where(Question.display_order == 1, Question.version == 1)).one()
    assert question.prompt_text.endswith("corregido (relleno de test).")
    assert len(question.answer_options) == 3


def _serve(db_session, question: Question) -> None:
    user = User(cognito_sub="import-test", email="import@example.test")
    db_session.add(user)
    db_session.flush()
    attempt = TestAttempt(user_id=user.id, tier=AttemptTier.FREE_REDUCED, questionnaire_version=1)
    db_session.add(attempt)
    db_session.flush()
    db_session.add(
        Response(
            test_attempt_id=attempt.id,
            question_id=question.id,
            selected_option_id=question.answer_options[0].id,
            answered_at=datetime.now(timezone.utc),
            display_order=1,
            option_order=option_ids(question),
        )
    )
    db_session.flush()


def test_question_with_responses_is_never_modified(db_session, tmp_path):
    load_bank(db_session, read_bank_csv(FIXTURE), version=1, activate=False)
    question = db_session.scalars(select(Question).where(Question.display_order == 1, Question.version == 1)).one()
    original_text = question.prompt_text
    _serve(db_session, question)

    headers, rows = read_rows()
    for row in rows:
        if row["question_id"] == "T01":
            row["option_text"] = row["option_text"] + " Cambiada."
    with pytest.raises(QuestionBankError) as excinfo:
        load_bank(db_session, read_bank_csv(write_csv(tmp_path, headers, rows)), version=1, activate=False)

    assert "La versión 1 ya tiene respuestas" in str(excinfo.value)
    db_session.expire_all()
    assert question.prompt_text == original_text
    assert all("Cambiada" not in o.option_text for o in question.answer_options)


def test_question_with_responses_is_never_removed(db_session, tmp_path):
    load_bank(db_session, read_bank_csv(FIXTURE), version=1, activate=False)
    question = db_session.scalars(select(Question).where(Question.display_order == 1, Question.version == 1)).one()
    _serve(db_session, question)

    headers, rows = read_rows()
    rows = [row for row in rows if row["question_id"] != "T01"]
    with pytest.raises(QuestionBankError) as excinfo:
        load_bank(db_session, read_bank_csv(write_csv(tmp_path, headers, rows)), version=1, activate=False)

    assert "La versión 1 ya tiene respuestas" in str(excinfo.value)
    assert db_session.query(Question).filter_by(version=1).count() == 8


def test_question_without_responses_missing_from_the_csv_is_removed(db_session, tmp_path):
    load_bank(db_session, read_bank_csv(FIXTURE), version=1, activate=False)
    headers, rows = read_rows()
    rows = [row for row in rows if row["question_id"] != "T02"]

    summary = load_bank(
        db_session, read_bank_csv(write_csv(tmp_path, headers, rows)), version=1, activate=False
    )

    assert (summary.removed, summary.unchanged) == (1, 7)
    assert db_session.query(Question).filter_by(version=1).count() == 7


def test_loading_one_version_leaves_other_versions_alone(db_session):
    bank = read_bank_csv(FIXTURE)
    load_bank(db_session, bank, version=1, activate=False)
    load_bank(db_session, bank[:3], version=2, activate=False)

    assert db_session.query(Question).filter_by(version=1).count() == 8
    assert db_session.query(Question).filter_by(version=2).count() == 3


# --- identity by (version, display_order) -------------------------------------------------------


def _db_state(db_session, version: int) -> list[tuple]:
    """The whole version as plain tuples, ordered by position, options included."""
    db_session.expire_all()
    questions = db_session.scalars(
        select(Question).where(Question.version == version).order_by(Question.display_order)
    ).all()
    return [
        (
            q.display_order,
            q.grouping_system,
            q.question_type,
            q.prompt_text,
            tuple((o.display_order, o.option_text, o.group_label) for o in q.answer_options),
        )
        for q in questions
    ]


def _bank_state(bank) -> list[tuple]:
    return sorted(
        (
            q.display_order,
            q.grouping_system,
            q.question_type,
            q.prompt_text,
            tuple((o.display_order, o.option_text, o.group_label) for o in q.options),
        )
        for q in bank
    )


def test_reimporting_a_reordered_csv_without_responses_leaves_exactly_the_new_csv(db_session, tmp_path):
    load_bank(db_session, read_bank_csv(FIXTURE), version=1, activate=False)

    # Reverse the bank: every question moves to another position, so position 1 now holds what
    # was position 8 (a Likert item of another system), and so on. Rows are shuffled too.
    headers, rows = read_rows()
    for row in rows:
        row["display_order"] = str(9 - int(row["display_order"]))
    rows.reverse()
    reordered = read_bank_csv(write_csv(tmp_path, headers, rows))

    summary = load_bank(db_session, reordered, version=1, activate=False)

    assert (summary.inserted, summary.removed) == (0, 0)
    assert summary.updated == 8
    assert _db_state(db_session, 1) == _bank_state(reordered)
    # No option outlived its question's old content, and none is left dangling.
    assert db_session.query(AnswerOption).join(Question).filter(Question.version == 1).count() == 32
    orphans = db_session.execute(
        text(
            "SELECT count(*) FROM answer_options o "
            "LEFT JOIN questions q ON q.id = o.question_id WHERE q.id IS NULL"
        )
    ).scalar()
    assert orphans == 0


@pytest.mark.parametrize("change", ["identical", "edit_an_unanswered_question", "reorder"])
def test_reimporting_a_version_with_responses_is_rejected_whole(db_session, tmp_path, change):
    load_bank(db_session, read_bank_csv(FIXTURE), version=1, activate=False)
    answered = db_session.scalars(
        select(Question).where(Question.display_order == 1, Question.version == 1)
    ).one()
    _serve(db_session, answered)
    before = _db_state(db_session, 1)

    headers, rows = read_rows()
    if change == "edit_an_unanswered_question":
        for row in rows:
            if row["question_id"] == "T05":
                row["prompt_text"] = "Enunciado de prueba 5, corregido (relleno de test)."
    elif change == "reorder":
        for row in rows:
            row["display_order"] = str(9 - int(row["display_order"]))

    with pytest.raises(QuestionBankError) as excinfo:
        load_bank(db_session, read_bank_csv(write_csv(tmp_path, headers, rows)), version=1, activate=True)

    message = str(excinfo.value)
    assert "La versión 1 ya tiene respuestas" in message
    assert "cargá el banco como una versión nueva" in message
    assert _db_state(db_session, 1) == before
    assert question_repository.active_versions(db_session) == []
