#!/usr/bin/env python3
"""
Load the filler question bank as questionnaire version 0.

    python scripts/seed_filler_bank.py            # loads into the database of APP_ENV
    python scripts/seed_filler_bank.py --dry-run  # shows what it would load, saves nothing

The filler has the real shape of bank v1, so everything built against it survives the real bank:
200 questions, 50 per grouping system, 163 scenario items with 3 options and 37 Likert items with
5 ordered options. Each scenario item covers its system's three groups exactly once, in shuffled
order (the position of an option must not give away its group). In each Likert item the five
options carry the same group. Deterministic for a given seed.

FILLER — every prompt and option says so in its own text. It is not the instrument, it must never
be mistaken for it, and it is version 0 so no attempt made against it mixes with bank v1 data.
It never names the grouping system or the group: that would leak the answer key to the browser.

Version 0 is activated only if no version is active yet, so re-seeding never pulls a real bank
out of service. Re-running is idempotent. Once an attempt has been served from version 0 it is
frozen like any other version, and re-seeding leaves it alone.
"""

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # run as a file from backend/

from app.db.models.enums import GROUPS_BY_SYSTEM, GroupingSystem, QuestionType  # noqa: E402
from app.repositories import question_repository  # noqa: E402
from app.services.question_bank import (  # noqa: E402
    BankOption,
    BankQuestion,
    QuestionBankError,
    format_summary,
    load_bank,
)
from scripts._db import database_url, describe, open_session, utf8_output  # noqa: E402

FILLER_VERSION = 0
DEFAULT_SEED = 20261006

QUESTIONS_PER_SYSTEM = 50
LIKERT_TOTAL = 37  # 163 scenario + 37 Likert = 200, as in bank v1

FILLER_NOTE = "Contenido de relleno: no es un ítem del banco v1 ni de ningún instrumento real."

# Option 5 is maximum agreement (decision 12 of the plan).
LIKERT_SCALE = (
    "Nada de acuerdo",
    "Poco de acuerdo",
    "Ni de acuerdo ni en desacuerdo",
    "Bastante de acuerdo",
    "Completamente de acuerdo",
)


def build_filler_bank(seed: int = DEFAULT_SEED) -> list[BankQuestion]:
    rng = random.Random(seed)
    systems = list(GroupingSystem)

    # 37 Likert items over 4 systems: one system gets 10, the others 9.
    likert_per_system = dict.fromkeys(systems, LIKERT_TOTAL // len(systems))
    for system in rng.sample(systems, LIKERT_TOTAL % len(systems)):
        likert_per_system[system] += 1

    # (system, type, groups in option order)
    specs: list[tuple[GroupingSystem, QuestionType, list[str]]] = []
    for system in systems:
        groups = list(GROUPS_BY_SYSTEM[system])
        n_likert = likert_per_system[system]
        for _ in range(QUESTIONS_PER_SYSTEM - n_likert):
            specs.append((system, QuestionType.SCENARIO, rng.sample(groups, len(groups))))
        offset = rng.randrange(len(groups))
        for i in range(n_likert):
            target = groups[(offset + i) % len(groups)]
            specs.append((system, QuestionType.MULTIPLE_CHOICE, [target] * len(LIKERT_SCALE)))

    # The bank's order must not give away the system either.
    rng.shuffle(specs)

    bank = []
    for number, (system, question_type, option_groups) in enumerate(specs, start=1):
        if question_type is QuestionType.SCENARIO:
            prompt = f"[RELLENO · versión 0] Ítem {number:03d}, de escenario. {FILLER_NOTE}"
            texts = [f"[RELLENO] Opción {letter} del ítem {number:03d}." for letter in "ABC"]
        else:
            prompt = (
                f"[RELLENO · versión 0] Ítem {number:03d}, afirmación para escala de acuerdo. "
                f"{FILLER_NOTE}"
            )
            texts = [f"[RELLENO] {k} · {label}" for k, label in enumerate(LIKERT_SCALE, start=1)]
        bank.append(
            BankQuestion(
                source_id=f"filler-{number:03d}",
                grouping_system=system,
                question_type=question_type,
                prompt_text=prompt,
                display_order=number,
                options=tuple(
                    BankOption(option_text=text, group_label=group, display_order=k)
                    for k, (text, group) in enumerate(zip(texts, option_groups), start=1)
                ),
            )
        )
    return bank


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Carga el banco de relleno como versión 0.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Semilla del generador.")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar el resultado sin guardar.")
    args = parser.parse_args(argv)

    bank = build_filler_bank(args.seed)
    url = database_url()
    with open_session(url) as session:
        if question_repository.version_has_responses(session, FILLER_VERSION):
            print(f"Base: {describe(url)}")
            print("La versión 0 ya tiene respuestas: el relleno no se recarga.")
            return 0
        active = question_repository.active_versions(session)
        activate = active in ([], [FILLER_VERSION])
        try:
            summary = load_bank(session, bank, version=FILLER_VERSION, activate=activate)
        except QuestionBankError as error:
            print("No se cargó el relleno:", file=sys.stderr)
            for problem in error.problems:
                print(f"  - {problem}", file=sys.stderr)
            return 1
        if args.dry_run:
            session.rollback()
        else:
            session.commit()

    print(f"Base: {describe(url)} · semilla {args.seed}")
    if args.dry_run:
        print("SIMULACIÓN (--dry-run): no se guardó nada.")
    if not activate:
        print(f"La versión 0 no se activó: ya hay una versión activa ({', '.join(map(str, active))}).")
    print(format_summary(summary))
    return 0


if __name__ == "__main__":
    utf8_output()
    sys.exit(main())
