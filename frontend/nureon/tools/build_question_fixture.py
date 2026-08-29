#!/usr/bin/env python3
"""
Build the questionnaire fixture consumed by MockApiService.

Two modes:

    # Real content, once Tobi hands over the CSV companion of the v1 bank
    python tools/build_question_fixture.py --csv "NureonAI Question Bank v1.csv" \
        > src/assets/mock/questions.sample.json

    # Placeholder content, for layout work before the CSV exists
    python tools/build_question_fixture.py --placeholder \
        > src/assets/mock/questions.sample.json

Both modes emit the same shape, so swapping one for the other touches no component.

CONTRACT NOTE — `grouping_system` and `group_label` are deliberately NOT emitted.
They exist in the database (see the data-model PDR) but must never reach the browser:
they are the answer key of a psychometric instrument, and shipping them lets anyone
read the mapping out of devtools and game the test. The client sends back a selected
option id and nothing else; the server resolves the group. Keep it that way when
MockApiService is replaced by the real ApiService.
"""

import argparse
import csv
import json
import random
import sys
import uuid

TOTAL_ITEMS = 40
# The v1 bank is 163 scenario / 37 Likert items -> ~81.5% / 18.5%.
SCENARIO_SHARE = 0.815

# ---------------------------------------------------------------------------
# CSV mode
# ---------------------------------------------------------------------------

# One row per question+answer pair. Adjust the right-hand side to the real
# headers once the file exists; the script fails loudly if they do not match.
COLUMNS = {
    "question_id": "question_id",
    "question_type": "question_type",
    "prompt_text": "prompt_text",
    "question_order": "display_order",
    "option_text": "option_text",
    "option_order": "option_display_order",
}


def from_csv(path, seed):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in COLUMNS.values() if c not in (reader.fieldnames or [])]
        if missing:
            sys.exit(
                "Estas columnas no están en el CSV: " + ", ".join(missing) +
                "\nColumnas encontradas: " + ", ".join(reader.fieldnames or []) +
                "\nAjustá el diccionario COLUMNS arriba en este script."
            )
        rows = list(reader)

    questions = {}
    for row in rows:
        qid = row[COLUMNS["question_id"]]
        q = questions.setdefault(qid, {
            "sourceId": qid,
            "questionType": row[COLUMNS["question_type"]].strip(),
            "promptText": row[COLUMNS["prompt_text"]].strip(),
            "order": int(row[COLUMNS["question_order"]] or 0),
            "options": [],
        })
        q["options"].append({
            "optionText": row[COLUMNS["option_text"]].strip(),
            "order": int(row[COLUMNS["option_order"]] or len(q["options"]) + 1),
        })

    pool = list(questions.values())
    rng = random.Random(seed)

    # Sample keeping the bank's real mix of item shapes, and always include the
    # longest prompt and the longest option so the layout is stress-tested.
    scenario = [q for q in pool if len(q["options"]) == 3]
    likert = [q for q in pool if len(q["options"]) == 5]
    n_scenario = round(TOTAL_ITEMS * SCENARIO_SHARE)
    picked = rng.sample(scenario, min(n_scenario, len(scenario)))
    picked += rng.sample(likert, min(TOTAL_ITEMS - len(picked), len(likert)))

    def longest(items, key):
        return max(items, key=key) if items else None

    worst_prompt = longest(pool, lambda q: len(q["promptText"]))
    worst_option = longest(pool, lambda q: max(len(o["optionText"]) for o in q["options"]))
    for extreme in (worst_prompt, worst_option):
        if extreme and extreme not in picked:
            picked[-1] = extreme

    rng.shuffle(picked)
    return picked, False


# ---------------------------------------------------------------------------
# Placeholder mode
# ---------------------------------------------------------------------------

# Filler that says out loud that it is filler, at the lengths a real Spanish item
# reaches, so a layout built against it survives the real bank. Deliberately not
# written as plausible questionnaire items: this content must never be mistaken
# for the real instrument, which is exactly the mistake the v1 rework corrected.

_SHORT = "Enunciado de ejemplo, corto, solo para verificar el layout."
_MEDIUM = ("Enunciado de ejemplo de longitud media, escrito para ocupar aproximadamente lo mismo "
           "que un ítem real del banco y verificar cómo se comporta la tipografía.")
_LONG = ("Enunciado de ejemplo deliberadamente largo, por encima del peor caso esperado del banco "
         "real, para comprobar que el bloque de la pregunta no desborda ni empuja las opciones "
         "fuera de la pantalla cuando el texto ocupa varias líneas seguidas en pantallas angostas.")

_OPT_SHORT = "Opción de ejemplo corta."
_OPT_MEDIUM = "Opción de ejemplo de longitud media, para ver cómo cae el texto dentro de la tarjeta."
_OPT_LONG = ("Opción de ejemplo larga, pensada para exceder el peor caso del banco real y confirmar "
             "que la tarjeta crece en altura sin romper la grilla ni recortar el texto.")

_LIKERT = [
    "Nada de acuerdo",
    "Poco de acuerdo",
    "Ni de acuerdo ni en desacuerdo",
    "Bastante de acuerdo",
    "Completamente de acuerdo",
]


def from_placeholder(seed):
    rng = random.Random(seed)
    prompts = [_SHORT, _MEDIUM, _MEDIUM, _MEDIUM, _LONG]
    options = [_OPT_SHORT, _OPT_MEDIUM, _OPT_MEDIUM, _OPT_LONG]

    n_scenario = round(TOTAL_ITEMS * SCENARIO_SHARE)
    items = []

    for i in range(n_scenario):
        # Guarantee the extremes appear early enough to be seen while developing.
        prompt = _LONG if i == 2 else rng.choice(prompts)
        opts = [_OPT_LONG if (i == 3 and k == 0) else rng.choice(options) for k in range(3)]
        items.append({
            "sourceId": f"placeholder-scenario-{i + 1}",
            "questionType": "scenario",
            "promptText": prompt,
            "order": 0,
            "options": [{"optionText": t, "order": k + 1} for k, t in enumerate(opts)],
        })

    for i in range(TOTAL_ITEMS - n_scenario):
        items.append({
            "sourceId": f"placeholder-likert-{i + 1}",
            "questionType": "multiple_choice",
            "promptText": rng.choice(prompts),
            "order": 0,
            "options": [{"optionText": t, "order": k + 1} for k, t in enumerate(_LIKERT)],
        })

    rng.shuffle(items)
    return items, True


# ---------------------------------------------------------------------------

def build(items, placeholder):
    questions = []
    for index, item in enumerate(items, start=1):
        questions.append({
            "id": str(uuid.uuid4()),
            "questionType": item["questionType"],
            "promptText": item["promptText"],
            "displayOrder": index,
            "options": [
                {
                    "id": str(uuid.uuid4()),
                    "optionText": o["optionText"],
                    "displayOrder": o["order"],
                }
                for o in sorted(item["options"], key=lambda o: o["order"])
            ],
        })

    payload = {
        "attempt": {
            "id": str(uuid.uuid4()),
            "tier": "free_reduced",
            "questionnaireVersion": 1,
            "status": "in_progress",
            "startedAt": "2026-08-29T12:00:00Z",
            "completedAt": None,
        },
        "questions": questions,
    }

    if placeholder:
        payload = {
            "_placeholder": True,
            "_warning": (
                "CONTENIDO DE RELLENO. No son ítems del banco v1 ni de ningún instrumento real. "
                "Sirven solo para verificar layout y longitudes de texto. No usar en capturas para "
                "el documento, ni en pruebas piloto, ni como base para escribir ítems reales. "
                "Regenerar con --csv apenas esté disponible el CSV del banco v1."
            ),
            **payload,
        }
    return payload


def main():
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--csv", help="CSV companion del banco v1 (una fila por pregunta+respuesta)")
    group.add_argument("--placeholder", action="store_true", help="Generar relleno para trabajar el layout")
    ap.add_argument("--seed", type=int, default=20260829, help="Semilla, para que el fixture sea reproducible")
    args = ap.parse_args()

    if args.csv:
        items, placeholder = from_csv(args.csv, args.seed)
    else:
        items, placeholder = from_placeholder(args.seed)

    json.dump(build(items, placeholder), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
