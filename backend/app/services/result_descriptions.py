"""`results.description_text` per eneatype: the one-sentence summary of each type.

A copy of `summary` in `frontend/nureon/src/app/resultados/eneatype-content.ts`, which is where the
text is written. `tests/test_result_descriptions.py` fails if the two drift apart.

Fixed per type: nothing in it depends on how the type was reached, or on any internal number.
"""

DESCRIPTIONS: dict[int, str] = {
    1: "Íntegro, exigente, ordenado y comprometido con hacer las cosas bien.",
    2: "Atento, afectuoso, generoso y pendiente de lo que necesitan los demás.",
    3: "Enérgico, eficaz, orientado a metas y atento a la impresión que causa.",
    4: "Sensible, creativo, profundo y fiel a su propia manera de ver las cosas.",
    5: "Curioso, observador, autónomo y de pocas palabras.",
    6: "Responsable, previsor, solidario y comprometido con su grupo.",
    7: "Alegre, inquieto, versátil y con muchas ganas de vivir cosas nuevas.",
    8: "Fuerte, directo, protector y con iniciativa para tomar el mando.",
    9: "Sereno, paciente, abierto y con facilidad para acercar a las personas.",
}


def description_for(eneatype: int) -> str:
    return DESCRIPTIONS[eneatype]
