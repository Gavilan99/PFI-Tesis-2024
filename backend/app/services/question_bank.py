"""Loading a question bank into `questions` and `answer_options`.

Shared by the filler seed (version 0) and the real-bank import. Both go through the same shape
validation, so the filler cannot drift from what the real bank must satisfy.

Messages are in Spanish: they are read by whoever runs the scripts.
"""

from collections import Counter
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.db.models import AnswerOption, Question
from app.db.models.enums import GROUPS_BY_SYSTEM, GroupingSystem, QuestionType
from app.repositories import question_repository

SCENARIO_OPTIONS = 3
LIKERT_OPTIONS = 5
# Bank v1 only has these two types. ORDERING and TEXT are valid in the schema, not in a bank load.
LOADABLE_TYPES = (QuestionType.SCENARIO, QuestionType.MULTIPLE_CHOICE)


@dataclass(frozen=True)
class BankOption:
    option_text: str
    group_label: str
    display_order: int


@dataclass(frozen=True)
class BankQuestion:
    source_id: str
    grouping_system: GroupingSystem
    question_type: QuestionType
    prompt_text: str
    display_order: int
    options: tuple[BankOption, ...]


class QuestionBankError(Exception):
    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("\n".join(problems))


@dataclass
class LoadSummary:
    version: int
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    removed: int = 0
    activated: bool = False
    active_versions: list[int] = field(default_factory=list)
    counts: dict = field(default_factory=dict)


def validate_bank(questions: list[BankQuestion]) -> list[str]:
    """Every structural rule a bank must satisfy before it touches the database."""
    problems: list[str] = []
    if not questions:
        return ["El banco no tiene preguntas."]

    order_counts = Counter(q.display_order for q in questions)
    for order, count in sorted(order_counts.items()):
        if count > 1:
            problems.append(f"El orden de pregunta {order} aparece en {count} preguntas.")

    for q in questions:
        where = f"Pregunta {q.source_id}"
        if q.question_type not in LOADABLE_TYPES:
            problems.append(
                f"{where}: tipo '{q.question_type.value}' fuera de alcance; "
                "el banco sólo admite 'scenario' y 'multiple_choice'."
            )
            continue
        if not q.prompt_text.strip():
            problems.append(f"{where}: el enunciado está vacío.")
        if q.display_order < 1:
            problems.append(f"{where}: el orden de pregunta tiene que ser 1 o mayor.")

        option_orders = Counter(o.display_order for o in q.options)
        if any(count > 1 for count in option_orders.values()):
            problems.append(f"{where}: hay órdenes de opción repetidos.")
        if any(o.display_order < 1 for o in q.options):
            problems.append(f"{where}: el orden de opción tiene que ser 1 o mayor.")
        if any(not o.option_text.strip() for o in q.options):
            problems.append(f"{where}: hay una opción con texto vacío.")

        system_groups = GROUPS_BY_SYSTEM[q.grouping_system]
        foreign = sorted({o.group_label for o in q.options} - set(system_groups))
        if foreign:
            problems.append(
                f"{where}: los grupos {', '.join(foreign)} no pertenecen al sistema "
                f"{q.grouping_system.value}."
            )

        groups = [o.group_label for o in q.options]
        if q.question_type is QuestionType.SCENARIO:
            if sorted(groups) != sorted(system_groups):
                problems.append(
                    f"{where}: un ítem de escenario tiene que tener {SCENARIO_OPTIONS} opciones que "
                    f"cubran {', '.join(system_groups)} exactamente una vez cada uno; "
                    f"tiene: {', '.join(groups) or 'ninguna'}."
                )
        else:
            if len(q.options) != LIKERT_OPTIONS:
                problems.append(
                    f"{where}: un ítem Likert tiene que tener {LIKERT_OPTIONS} opciones; "
                    f"tiene {len(q.options)}."
                )
            if len(set(groups)) > 1:
                problems.append(
                    f"{where}: las opciones de un ítem Likert tienen que llevar todas el mismo "
                    f"grupo; mezcla {', '.join(sorted(set(groups)))}."
                )
    return problems


def load_bank(
    session: Session, questions: list[BankQuestion], *, version: int, activate: bool
) -> LoadSummary:
    """Bring `version` in the database to exactly `questions`. Does not commit.

    A question is identified by its position in the bank: re-importing leaves identical questions
    alone and rewrites the rest in place. That is only safe while no attempt has been served from
    the version, so a version with any response row is frozen whole: the load is rejected before
    anything is compared, and a changed bank has to come in as a new version.
    """
    problems = validate_bank(questions)
    if problems:
        raise QuestionBankError(problems)

    if question_repository.version_has_responses(session, version):
        raise QuestionBankError(
            [
                f"La versión {version} ya tiene respuestas: no se modifica, ni siquiera para "
                "reordenarla o recargarla igual. Si el banco cambió, cargá el banco como una "
                "versión nueva."
            ]
        )

    existing = {q.display_order: q for q in question_repository.questions_for_version(session, version)}
    version_was_active = any(q.is_active for q in existing.values())

    inserts: list[BankQuestion] = []
    updates: list[tuple[Question, BankQuestion]] = []
    unchanged = 0

    for bank_question in questions:
        current = existing.pop(bank_question.display_order, None)
        if current is None:
            inserts.append(bank_question)
        elif _same_content(current, bank_question):
            unchanged += 1
        else:
            updates.append((current, bank_question))
    removals = list(existing.values())

    question_repository.delete_options(session, [q.id for q in removals] + [q.id for q, _ in updates])
    question_repository.delete_questions(session, [q.id for q in removals])

    for question, bank_question in updates:
        question.grouping_system = bank_question.grouping_system
        question.question_type = bank_question.question_type
        question.prompt_text = bank_question.prompt_text
        session.add_all(_options_for(question, bank_question))

    for bank_question in inserts:
        question = Question(
            grouping_system=bank_question.grouping_system,
            question_type=bank_question.question_type,
            prompt_text=bank_question.prompt_text,
            version=version,
            display_order=bank_question.display_order,
            is_active=version_was_active,
        )
        session.add(question)
        session.flush()
        session.add_all(_options_for(question, bank_question))

    session.flush()
    if activate:
        question_repository.activate_version(session, version)
        session.flush()
    session.expire_all()

    return LoadSummary(
        version=version,
        inserted=len(inserts),
        updated=len(updates),
        unchanged=unchanged,
        removed=len(removals),
        activated=activate,
        active_versions=question_repository.active_versions(session),
        counts=question_repository.version_counts(session, version),
    )


def _options_for(question: Question, bank_question: BankQuestion) -> list[AnswerOption]:
    return [
        AnswerOption(
            question_id=question.id,
            option_text=o.option_text,
            group_label=o.group_label,
            display_order=o.display_order,
        )
        for o in bank_question.options
    ]


def _same_content(question: Question, bank_question: BankQuestion) -> bool:
    current_options = sorted(
        (o.display_order, o.option_text, o.group_label) for o in question.answer_options
    )
    bank_options = sorted(
        (o.display_order, o.option_text, o.group_label) for o in bank_question.options
    )
    return (
        question.grouping_system == bank_question.grouping_system
        and question.question_type == bank_question.question_type
        and question.prompt_text == bank_question.prompt_text
        and current_options == bank_options
    )


def format_counts(counts: dict) -> str:
    lines = [f"Preguntas: {counts['questions']}"]
    lines.append("  Por sistema:")
    for system in GroupingSystem:
        lines.append(f"    {system.value:<22}{counts['questions_by_system'].get(system.value, 0):>5}")
    lines.append("  Por tipo:")
    for question_type in QuestionType:
        lines.append(
            f"    {question_type.value:<22}{counts['questions_by_type'].get(question_type.value, 0):>5}"
        )
    lines.append(f"Opciones: {counts['options']}")
    lines.append("  Por grupo:")
    for system, groups in GROUPS_BY_SYSTEM.items():
        for group in groups:
            count = counts["options_by_group"].get((system.value, group), 0)
            lines.append(f"    {system.value + ' / ' + group:<40}{count:>5}")
    return "\n".join(lines)


def format_summary(summary: LoadSummary) -> str:
    lines = [
        f"Versión {summary.version}",
        f"  Nuevas: {summary.inserted} · Modificadas: {summary.updated} · "
        f"Sin cambios: {summary.unchanged} · Quitadas: {summary.removed}",
        f"  Versiones activas después de la carga: "
        f"{', '.join(map(str, summary.active_versions)) or 'ninguna'}",
        format_counts(summary.counts),
    ]
    return "\n".join(lines)
