#!/usr/bin/env python3
"""
Import the real question bank from its CSV companion into `questions` and `answer_options`.

    python scripts/import_question_bank.py --csv "NureonAI Question Bank v1.csv" --version 1 --dry-run
    python scripts/import_question_bank.py --csv "NureonAI Question Bank v1.csv" --version 1 --activate

One row per question+answer pair. The CSV's real headers are not known yet (PA-3): adjust COLUMNS
below. If a header is missing, the script stops and names it before reading any row.

The bank labels systems and groups in Spanish; the maps below translate them to the canonical
vocabulary (CLAUDE.md, "Vocabulario canónico"). An unknown label stops the load.

Rules that stop the load: an unknown system or group label; a group that does not belong to the
item's system; a scenario item that does not cover its system's three groups exactly once; a
Likert item without five options or mixing groups.

Idempotent: re-importing the same version leaves identical questions alone. A question that already
has responses is never modified nor removed; if the CSV would require it, nothing is saved.
`--activate` activates this version and deactivates every other one in the same transaction.
`--dry-run` runs the whole load and rolls it back.

Version 0 is reserved for filler (scripts/seed_filler_bank.py).
"""

import argparse
import csv
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # run as a file from backend/

from app.db.models.enums import GroupingSystem, QuestionType  # noqa: E402
from app.services.question_bank import (  # noqa: E402
    BankOption,
    BankQuestion,
    QuestionBankError,
    format_summary,
    load_bank,
    validate_bank,
)
from scripts._db import database_url, describe, open_session  # noqa: E402

# ---------------------------------------------------------------------------------------------
# Column map: logical field -> header in the CSV. Adjust the right-hand side to the real headers.
# The first six are the ones the frontend's build_question_fixture.py already assumes.
# ---------------------------------------------------------------------------------------------
COLUMNS = {
    "question_id": "question_id",
    "question_type": "question_type",
    "prompt_text": "prompt_text",
    "question_order": "display_order",
    "option_text": "option_text",
    "option_order": "option_display_order",
    "grouping_system": "grouping_system",
    "group_label": "group_label",
}

# Bank label -> canonical value. Matching ignores case, surrounding spaces and Unicode form,
# never accents: "Retraida" is not "Retraída".
GROUPING_SYSTEMS = {
    "Centros de Inteligencia": GroupingSystem.INTELLIGENCE_CENTERS,
    "Conjunto Horneviano": GroupingSystem.HORNEVIAN,
    "Conjunto Armónico": GroupingSystem.HARMONIC,
    "Conjunto de Relaciones Objetales": GroupingSystem.OBJECT_RELATIONS,
}

GROUP_LABELS = {
    "Cuerpo": "gut",
    "Corazón": "heart",
    "Mente": "head",
    "Asertiva": "assertive",
    "Complaciente": "compliant",
    "Retraída": "withdrawn",
    "Positiva": "positive_outlook",
    "Competente": "competency",
    "Reactiva": "reactive",
    "Apego": "attachment",
    "Frustración": "frustration",
    "Rechazo": "rejection",
}

QUESTION_TYPES = {
    "scenario": QuestionType.SCENARIO,
    "multiple_choice": QuestionType.MULTIPLE_CHOICE,
}


class CsvFormatError(Exception):
    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("\n".join(problems))


def _key(label: str) -> str:
    return unicodedata.normalize("NFC", label).strip().casefold()


_SYSTEMS = {_key(k): v for k, v in GROUPING_SYSTEMS.items()}
_GROUPS = {_key(k): v for k, v in GROUP_LABELS.items()}
_TYPES = {_key(k): v for k, v in QUESTION_TYPES.items()}


def read_bank_csv(path: Path) -> list[BankQuestion]:
    """Parse and translate the CSV. Raises CsvFormatError listing every problem found."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []
        missing = [header for header in COLUMNS.values() if header not in headers]
        if missing:
            raise CsvFormatError(
                [
                    "Faltan columnas en el CSV: " + ", ".join(missing) + ".",
                    "Columnas encontradas: " + (", ".join(headers) or "ninguna") + ".",
                    "Ajustá el diccionario COLUMNS arriba de scripts/import_question_bank.py.",
                ]
            )
        rows = [(reader.line_num, row) for row in reader]

    problems: list[str] = []
    questions: dict[str, dict] = {}

    for line, row in rows:
        def cell(field: str) -> str:
            return (row.get(COLUMNS[field]) or "").strip()

        where = f"Línea {line}"
        source_id = cell("question_id")
        if not source_id:
            problems.append(f"{where}: falta el id de pregunta.")
            continue

        system = _SYSTEMS.get(_key(cell("grouping_system")))
        if system is None:
            problems.append(f"{where}: sistema desconocido '{cell('grouping_system')}'.")
        group = _GROUPS.get(_key(cell("group_label")))
        if group is None:
            problems.append(f"{where}: grupo desconocido '{cell('group_label')}'.")
        question_type = _TYPES.get(_key(cell("question_type")))
        if question_type is None:
            problems.append(f"{where}: tipo de pregunta desconocido '{cell('question_type')}'.")
        question_order = _int(cell("question_order"), where, "orden de pregunta", problems)
        option_order = _int(cell("option_order"), where, "orden de opción", problems)
        if None in (system, group, question_type, question_order, option_order):
            continue

        fields = {
            "grouping_system": system,
            "question_type": question_type,
            "prompt_text": cell("prompt_text"),
            "display_order": question_order,
        }
        question = questions.setdefault(source_id, {**fields, "options": []})
        for name, value in fields.items():
            if question[name] != value:
                problems.append(
                    f"{where}: la pregunta {source_id} cambia de '{name}' respecto de sus filas "
                    "anteriores."
                )
        question["options"].append(
            BankOption(option_text=cell("option_text"), group_label=group, display_order=option_order)
        )

    if not rows:
        problems.append("El CSV no tiene filas.")
    if problems:
        raise CsvFormatError(problems)

    return [
        BankQuestion(
            source_id=source_id,
            grouping_system=q["grouping_system"],
            question_type=q["question_type"],
            prompt_text=q["prompt_text"],
            display_order=q["display_order"],
            options=tuple(sorted(q["options"], key=lambda o: o.display_order)),
        )
        for source_id, q in questions.items()
    ]


def _int(raw: str, where: str, name: str, problems: list[str]) -> int | None:
    try:
        return int(raw)
    except ValueError:
        problems.append(f"{where}: el {name} '{raw}' no es un número entero.")
        return None


def _report(title: str, problems: list[str]) -> int:
    print(title, file=sys.stderr)
    for problem in problems:
        print(f"  - {problem}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Importa el banco de preguntas desde su CSV.")
    parser.add_argument("--csv", required=True, type=Path, help="CSV del banco, una fila por opción.")
    parser.add_argument("--version", required=True, type=int, help="Versión del cuestionario (1 o mayor).")
    parser.add_argument("--dry-run", action="store_true", help="Validar y simular la carga sin guardar.")
    parser.add_argument(
        "--activate", action="store_true", help="Activar esta versión y desactivar las demás."
    )
    args = parser.parse_args(argv)

    if args.version < 1:
        return _report(
            "No se importó nada:",
            ["La versión 0 está reservada para el relleno (scripts/seed_filler_bank.py)."],
        )

    try:
        bank = read_bank_csv(args.csv)
    except CsvFormatError as error:
        return _report(f"No se importó nada. Problemas en {args.csv}:", error.problems)

    problems = validate_bank(bank)
    if problems:
        return _report(f"No se importó nada. El banco en {args.csv} no tiene la forma esperada:", problems)

    url = database_url()
    with open_session(url) as session:
        try:
            summary = load_bank(session, bank, version=args.version, activate=args.activate)
        except QuestionBankError as error:
            return _report("No se importó nada:", error.problems)
        if args.dry_run:
            session.rollback()
        else:
            session.commit()

    print(f"CSV: {args.csv} · {len(bank)} preguntas leídas")
    print(f"Base: {describe(url)}")
    if args.dry_run:
        print("SIMULACIÓN (--dry-run): se validó y se simuló la carga; no se guardó nada.")
    print(format_summary(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
