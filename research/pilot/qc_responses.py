# -*- coding: utf-8 -*-
"""Control de calidad por respondente, sobre la salida de parse_form_export.py.

    python3 qc_responses.py responses_wide.csv

QUÉ MIDE
--------
**Estilo de respuesta**: concentración en una sola ancla del Likert, en una sola
posición de los escenarios, rachas de la misma opción, y concentración intra-conjunto.

NO DICE QUE LA RESPUESTA SEA MALA. Una versión anterior de este script las llamaba
"patrones que indican que la persona dejó de leer" y marcaba las filas como REVISAR
con sentido de descarte. **Eso daba por sentado que el estilo es ruido, que es
justamente lo que está en discusión**: si el estilo de respuesta covaría con el tipo,
entonces es señal, y excluir esas filas borra dato y sesga la muestra contra los tipos
que responden así. A 2026-09-27 hay evidencia preliminar de que el tipo 6 concentra
más que el resto (Mann-Whitney p=0.006, n=4).

Las filas marcadas se **señalan**, no se descartan. La decisión de excluir —si se
toma— es del analista y se declara.

CONCENTRACIÓN INTRA-CONJUNTO — agregado 2026-09-22
--------------------------------------------------
Los chequeos de arriba miran la FORMA de la respuesta (posición, ancla, racha) y son
ciegos al contenido a propósito. Eso los dejó pasar el caso más extremo del piloto:
un respondente eligió su propio grupo en los 96 escenarios y marcó el máximo en los 49
Likert de su grupo — y como la posición está desconfundida del grupo (χ²=0), fue variando
posición y ancla mientras respondía por regla. **Usó 5/5 anclas y 3/3 posiciones: el
chequeo de forma dijo "ok".**

El agregado mide cuánto se concentra cada persona en UN grupo dentro de cada conjunto,
**sin decir cuál** — así detecta la respuesta estereotipada sin revelar el perfil ni
romper la ceguera de la tipificación. Umbral fijado por principio, no ajustado a los
datos: elegir el mismo grupo en los 24 ítems de un conjunto no es un perfil, es una
regla de respuesta.

QUÉ NO IMPRIME, Y POR QUÉ
-------------------------
**No imprime el perfil de nadie** — ni qué grupos eligió, ni hacia dónde se inclina.
Sólo dice si hay o no patrón mecánico, y cuán concentrado respondió.

La tipificación experta tiene que ser ciega **respecto de las respuestas**, no sólo
respecto del prior sellado. Si el entrevistador ve el perfil de respuestas de alguien
antes de tipificarlo, las features y la etiqueta dejan de producirse por separado, y
toda la precisión que se reporte después mide esa contaminación y no el instrumento.
Por eso el corte está acá y no en la prudencia de quien lee la salida.

El perfil por grupo se analiza **después** de que la tipificación de esa persona esté
cerrada en el archivo B, con `--perfil` y a conciencia.
"""
import csv, sys, io, collections

NOT_ASKED = "NO_PREGUNTADO"
LIKERT_N = 5          # 5 anclas
STRAIGHT_LIKERT = 0.60   # una sola ancla en 60%+ de los Likert
STRAIGHT_SCEN   = 0.60   # una sola posición en 60%+ de los escenarios
RUN_ALERT       = 10     # racha de la misma opción
CONC_ALERTA     = 1.00   # un grupo se lleva UN CONJUNTO ENTERO: no es perfil, es regla
CONC_VIGILA     = 0.80   # media de concentración sobre los cuatro conjuntos


def load_bank(bank_path):
    fmt, sistema, opciones = {}, {}, collections.defaultdict(list)
    for r in csv.DictReader(io.open(bank_path, encoding="utf-8")):
        fmt[r["question_id"]] = r["format"]
        sistema[r["question_id"]] = r["grouping_system"]
        opciones[r["question_id"]].append(r)
    for q in opciones:
        opciones[q].sort(key=lambda r: int(r["display_order"]))
    return fmt, sistema, opciones


def concentracion(r, qs, fmt, sistema, opciones):
    """Por conjunto: qué fracción de los escenarios se llevó el grupo más elegido.
    No devuelve CUÁL grupo — a propósito."""
    por_conj = collections.defaultdict(list)
    for q in qs:
        if fmt[q] != "scenario" or r[q] == NOT_ASKED:
            continue
        por_conj[sistema[q]].append(opciones[q][int(r[q]) - 1]["group_label"])
    out = {}
    for conj, picks in por_conj.items():
        if picks:
            out[conj] = collections.Counter(picks).most_common(1)[0][1] / len(picks)
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); return 2
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    bank = os.path.join(os.path.dirname(here), "bank", "NureonAI Prototype v4.1.csv")
    fmt, sistema, opciones = load_bank(bank)

    rows = list(csv.DictReader(io.open(args[0], encoding="utf-8")))
    qs = [c for c in rows[0] if c.startswith("Q")]
    print(f"{len(rows)} respondentes · {len(qs)} ítems\n")

    problems = 0
    for r in rows:
        rid = r["respondent_id"] or "(sin código)"
        lik = [r[q] for q in qs if fmt[q] == "likert" and r[q] != NOT_ASKED]
        scn = [r[q] for q in qs if fmt[q] == "scenario" and r[q] != NOT_ASKED]
        seq = [r[q] for q in qs if r[q] != NOT_ASKED]

        flags = []

        if lik:
            top, n = collections.Counter(lik).most_common(1)[0]
            if n / len(lik) >= STRAIGHT_LIKERT:
                flags.append(f"una sola ancla en {n}/{len(lik)} Likert ({n/len(lik):.0%})")
        if scn:
            top, n = collections.Counter(scn).most_common(1)[0]
            if n / len(scn) >= STRAIGHT_SCEN:
                flags.append(f"una sola posición en {n}/{len(scn)} escenarios ({n/len(scn):.0%})")

        run = best = 1
        for i in range(1, len(seq)):
            run = run + 1 if seq[i] == seq[i - 1] else 1
            best = max(best, run)
        if best >= RUN_ALERT:
            flags.append(f"racha de {best} respuestas idénticas seguidas")

        conc = concentracion(r, qs, fmt, sistema, opciones)
        if conc:
            media = sum(conc.values()) / len(conc)
            llenos = [c for c, v in conc.items() if v >= CONC_ALERTA]
            if llenos:
                flags.append(f"{len(llenos)} conjunto(s) con UN SOLO grupo en el 100% "
                             f"de sus escenarios — respuesta por regla, no perfil")
            elif media >= CONC_VIGILA:
                flags.append(f"concentración media {media:.0%} sobre los cuatro conjuntos")

        faltan = sum(1 for q in qs if r[q] == NOT_ASKED)

        # Métricas sin contenido: dicen si respondió mecánicamente, no qué respondió.
        ent_l = len(set(lik)); ent_s = len(set(scn))
        estado = "ESTILO" if flags else "-"
        print(f"{rid:12} {estado:8} "
              f"likert {len(lik):3} (usó {ent_l}/{LIKERT_N} anclas) · "
              f"escenario {len(scn):3} (usó {ent_s} posiciones) · "
              f"concentr. media {sum(conc.values())/len(conc):.0%} · "
              f"racha máx {best} · sin responder {faltan}")
        for f in flags:
            print(f"             x {f}")
            problems += 1

    print()
    if problems:
        print(f"{problems} señal(es) de estilo marcado. NO son motivo de exclusión por sí "
              f"solas: el estilo puede ser señal del tipo. Ver el docstring.")
    else:
        print("Sin estilo marcado. (No dice nada sobre el contenido — a propósito.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
