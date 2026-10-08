"""PROVISIONAL — `results.description_text` per eneatype. Not the final wording.

Copied as is from the one-sentence `summary` of each eneatype in the frontend,
`frontend/nureon/src/app/resultados/eneatype-content.ts` (branch `redesign/frontend`), which marks
them as placeholders too. Not rewritten and not improved here: the final text is a separate task,
and today the frontend does not even read this field.

Fixed per type: nothing in it depends on how the type was reached, or on any internal number.
"""

PROVISIONAL_DESCRIPTIONS: dict[int, str] = {
    1: "Principista, con propósito, autocontrolado y perfeccionista.",
    2: "Cálido, cercano, generoso y complaciente con los demás.",
    3: "Seguro de sí mismo, ambicioso, orientado a resultados y consciente de su imagen.",
    4: "Creativo, expresivo, introspectivo y emocionalmente honesto.",
    5: "Analítico, independiente, perceptivo y reservado.",
    6: "Comprometido, responsable, cooperativo y alerta a los riesgos.",
    7: "Optimista, espontáneo, curioso y siempre buscando la próxima experiencia.",
    8: "Seguro, decidido, protector y con fuerte liderazgo.",
    9: "Tranquilo, conciliador, empático y capaz de ver todas las perspectivas.",
}


def description_for(eneatype: int) -> str:
    return PROVISIONAL_DESCRIPTIONS[eneatype]
