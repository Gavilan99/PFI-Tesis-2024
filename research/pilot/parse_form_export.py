# -*- coding: utf-8 -*-
"""Turns a Google Forms response export into the training-shape matrix.

    python3 parse_form_export.py "respuestas.csv"
    python3 parse_form_export.py "respuestas.csv" --out responses_wide.csv

WHAT IT DOES
------------
Forms exports one column per question, using the *question title* as the header.
Because make_form.gs puts the question_id first ("Q001 — ¿...?"), the id can be
recovered from each header and every answer mapped back to the locked bank.

Output: one row per respondent, one column per question_id, values = the option's
index within that question (1..n), plus NO_PREGUNTADO for anything unanswered.
That is the encoding the classifiers expect — see the Consequences Addendum
2026-08-17 (b) in "PDR — NureonAI 4-Classifier ML Design".

RUN THIS ON THE PILOT EXPORT (n=2–3) BEFORE RECRUITING AT VOLUME.
A broken mapping found at n=60 cannot be recovered; found at n=3 it costs an hour.

POR QUÉ HAY UNA HUELLA DEL BANCO
--------------------------------
El prototipo numera sus ítems Q001–Q145 y el banco v1 numera los suyos Q001–Q200.
**Los ids se pisan y no significan lo mismo en los dos**: de los 145 ids compartidos,
CERO comparten enunciado. Si este script apunta al banco equivocado, todas las
columnas del export matchean igual por id — `missing` da vacío, `extra` da vacío —
y el error aparece disfrazado de "130 respuestas no coincidieron con ninguna opción".
Peor: 8 de los 145 son Likert y sus cinco anclas son idénticas en los dos bancos, así
que esos ocho **validarían igual** y entrarían al CSV de entrenamiento con el índice
de la pregunta equivocada.

Por eso el banco se verifica por huella (ids + orden + texto de opción) y no por
nombre de archivo. Si la huella no coincide, el script se detiene y dice cuál es el
problema, en vez de dejarlo aparecer 130 renglones más abajo con el diagnóstico
equivocado.

CAMBIOS DE REDACCIÓN A MITAD DE LA RECOLECCIÓN (v4.1.1)
------------------------------------------------------
Ver «PDR — NureonAI Mid-Collection Rewording of Observed Items». Algunas opciones se
reescribieron en el formulario vivo SIN cambiar de id: es el mismo ítem, bajo el supuesto
de que se entiende lo mismo. `bank_aliases.json` lista, para cada opción cambiada, el texto
viejo y el nuevo. El banco base sigue siendo v4.1 y su huella sigue verificándose igual.

  · Las dos redacciones de una opción cuentan como la MISMA posición (1..n).
  · Cada texto «viejo» del archivo tiene que coincidir exactamente con el banco: si no
    coincide, el archivo se armó contra otro banco y el script se detiene.
  · Como Google guarda cada respuesta con el texto que tenía la opción al enviarla, en el
    export conviven las redacciones. Por eso se escribe `responses_version.csv`: qué
    versión respondió cada persona. Es lo que permite verificar el supuesto con los datos.
  · Hay más de una ronda de cambios (v4.1.1: 8 ítems en observación; v4.1.2: revisión
    general), cargadas en fechas distintas. El estado se registra POR VERSIÓN —viejo /
    nuevo / mixta / indeterminada—: quien respondió entre una carga y otra tiene la v4.1.1
    nueva y la v4.1.2 vieja, y eso no es «mixta». `version_banco` resume: la última versión
    respondida con texto nuevo, «mixta» si dentro de una misma versión aparecen los dos
    textos (retomó un borrador a mitad de una carga), o v4.1.
"""
import csv, sys, os, re, collections, io, hashlib

_SRC = os.path.dirname(os.path.abspath(__file__))
# Datos privados fuera del repositorio (ver README): export, correcciones de códigos y salidas.
HERE = os.environ.get("NUREON_DATA", os.path.join(_SRC, "data"))
BANK_DIR = os.path.join(os.path.dirname(_SRC), "bank")
BANK = os.path.join(BANK_DIR, "NureonAI Prototype v4.1.csv")

# Huella de lo único que este script consume: (question_id, display_order, option_text).
# El banco está congelado — build.py lo reescribe idéntico mientras no cambien los
# ítems. Si esto salta, o estás apuntando a otro banco, o el banco cambió DESPUÉS de
# recolectar respuestas, y en ese caso las respuestas ya recolectadas no son válidas.
BANK_FINGERPRINT = "8e8b5017ea4e4723fe0b2495fb63a48803ae83d57007ed0ee8f106145bd28dea"
BANK_EXPECT_QUESTIONS = 145
BANK_EXPECT_ROWS = 533

# Qué ítems se pusieron efectivamente delante del respondente. Los que están en el
# banco y NO en esta lista se esperan ausentes del export y se codifican
# NO_PREGUNTADO — es la codificación de features diseñada, no una falla. Lo escribe
# make_subset.py.
#
# PARA EL PILOTO DEL PROTOTIPO: None — se administran los 145 completos
# (~48 min a 20 s/ítem). La maquinaria de subset queda intacta por si vuelve a hacer
# falta; entonces esto apunta al .txt de ids que escriba make_subset.py.
ADMIN_IDS = None

NOT_ASKED = "NO_PREGUNTADO"
QID_RE = re.compile(r"^\s*(Q\d{3})\b")
CODE_RE = re.compile(r"^R\d{3}$")

# Correcciones del campo CODIGO. Ver code_fixes.json: el dato crudo no se edita nunca
# —el export se vuelve a bajar y la edición se perdería— así que la corrección vive
# acá, fechada, y el parser la anuncia cada vez que la aplica.
FIXES_PATH = os.path.join(HERE, "code_fixes.json")

# Redacciones nuevas de opciones (v4.1.1). Ver el docstring y el PDR.
ALIASES_PATH = os.path.join(BANK_DIR, "bank_aliases.json")


def cargar_aliases(bank):
    """Devuelve {(qid, display_order): (texto_nuevo, versión)} y la versión más reciente.
    Valida contra el banco."""
    if not os.path.exists(ALIASES_PATH):
        return {}, None
    import json
    data = json.load(io.open(ALIASES_PATH, encoding="utf-8"))
    nuevos, errores = {}, []
    for c in data.get("cambios", []):
        q = c["question_id"]
        if q not in bank:
            errores.append(f"{q}: no existe en el banco")
            continue
        if c.get("display_order") is None:          # enunciado: no interviene en el mapeo
            if bank[q][0]["prompt"].strip() != c["viejo"].strip():
                errores.append(f"{q} enunciado: el texto viejo no coincide con el banco")
            continue
        k = int(c["display_order"])
        opt = next((o for o in bank[q] if int(o["display_order"]) == k), None)
        if opt is None or opt["option_text"].strip() != c["viejo"].strip():
            errores.append(f"{q} opción {k}: el texto viejo no coincide con el banco")
            continue
        otros = {o["option_text"].strip() for o in bank[q] if int(o["display_order"]) != k}
        if c["nuevo"].strip() in otros:
            errores.append(f"{q} opción {k}: el texto nuevo es igual a otra opción del ítem")
            continue
        nuevos[(q, k)] = (c["nuevo"].strip(), c.get("version") or data.get("version"))
    if errores:
        raise SystemExit("bank_aliases.json NO coincide con el banco — no se parsea nada.\n  "
                         + "\n  ".join(errores))
    return nuevos, data.get("version")


def cargar_fixes():
    if not os.path.exists(FIXES_PATH):
        return [], []
    import json
    data = json.load(io.open(FIXES_PATH, encoding="utf-8"))
    por_texto, por_ts = [], []
    for f in data.get("fixes", []):
        if f.get("excluir"):
            continue                                   # exclusiones por código: ver cargar_exclusiones
        if f.get("submitted") is not None:
            por_texto.append((str(f["submitted"]).strip().casefold(), f))
        elif f.get("timestamp"):
            por_ts.append((str(f["timestamp"]).strip(), f))
    return por_texto, por_ts


def cargar_exclusiones():
    """Códigos excluidos del análisis, con su motivo: {"excluir": "R###", "motivo": ..., "fecha": ...}.
    Se aplican DESPUÉS de las correcciones de código. La respuesta sigue en el export; sólo no entra a
    responses_wide.csv. Criterio vigente (plan §4): sólo se excluye una respuesta SIN VARIACIÓN —la
    misma posición en todos los escenarios y la misma ancla en todos los Likert—, porque no contiene
    información. El estilo marcado, si varía, NO es motivo de exclusión."""
    if not os.path.exists(FIXES_PATH):
        return {}
    import json
    data = json.load(io.open(FIXES_PATH, encoding="utf-8"))
    return {str(f["excluir"]).strip().upper(): f for f in data.get("fixes", []) if f.get("excluir")}

# Covariables de familiaridad, al final del formulario. NO son ítems del banco: no
# entran al vector de features ni cuentan para completitud. Se arrastran como columnas
# propias porque son la razón de ser de las tres preguntas — permiten reportar la
# precisión PARTIDA POR FAMILIARIDAD. Si se perdieran acá, agregarlas al form no habría
# servido para nada. Texto literal, no índice: son para analizar, no para entrenar.
META_RE = re.compile(r"^\s*(META\d)\b")
META_COLS = {"META1": "meta_familiaridad",
             "META2": "meta_tipo_autopercibido",
             "META3": "meta_intento_adivinar"}

# Valores esperados, EXACTOS, como están cargados en el formulario vivo.
# Esto no es ceremonia: las META se cargaron a mano y se editaron a mano, así que la
# redacción del form y la del script pueden separarse sin que nadie se entere. Si eso
# pasa, "Algo, de oído" y "Algo, de oídas" se vuelven DOS categorías y el corte por
# familiaridad —lo único para lo que existen estas preguntas— queda partido en dos
# buckets que deberían ser uno. El chequeo avisa; no corrige ni normaliza nada.
META_EXPECTED = {
    "META1": {"Nada", "Algo, de oído", "Bastante", "Mucho, lo estudié"},
    "META2": {"Tipo 1", "Tipo 2", "Tipo 3", "Tipo 4", "Tipo 5", "Tipo 6",
              "Tipo 7", "Tipo 8", "Tipo 9",
              "Dudo entre dos", "No sé / no me considero de ninguno"},
    "META3": {"No, en ningún momento", "Alguna vez", "Bastante seguido"},
}


def fingerprint(rows):
    """Huella de los campos que el mapeo usa. Insensible al orden de las filas."""
    trip = sorted((r["question_id"], r["display_order"], r["option_text"].strip())
                  for r in rows)
    h = hashlib.sha256()
    for t in trip:
        h.update(("\x1f".join(t) + "\x1e").encode("utf-8"))
    return h.hexdigest()


def load_bank(path=BANK):
    if not os.path.exists(path):
        raise SystemExit(f"no existe el banco: {path}")
    with io.open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    bank = collections.OrderedDict()
    for r in rows:
        bank.setdefault(r["question_id"], []).append(r)
    for qid in bank:
        bank[qid].sort(key=lambda r: int(r["display_order"]))

    got = fingerprint(rows)
    if (got != BANK_FINGERPRINT
            or len(bank) != BANK_EXPECT_QUESTIONS
            or len(rows) != BANK_EXPECT_ROWS):
        raise SystemExit(
            "BANCO EQUIVOCADO O MODIFICADO — no se parsea nada.\n"
            f"  archivo   : {os.path.basename(path)}\n"
            f"  esperado  : {BANK_EXPECT_QUESTIONS} preguntas / {BANK_EXPECT_ROWS} filas / "
            f"{BANK_FINGERPRINT[:16]}…\n"
            f"  encontrado: {len(bank)} preguntas / {len(rows)} filas / {got[:16]}…\n"
            "  Ojo: los ids Q001… existen en los dos bancos y NO significan lo mismo.\n"
            "  Si el banco cambió a propósito, las respuestas recolectadas contra el\n"
            "  anterior no son válidas: actualizá BANK_FINGERPRINT a conciencia.")
    return bank


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    export_path = args[0]
    out_path = os.path.join(HERE, "responses_wide.csv")   # en la carpeta de datos, nunca en el repo
    for a in sys.argv[1:]:
        if a.startswith("--out="):
            out_path = a.split("=", 1)[1]

    bank = load_bank()
    aliases, alias_version = cargar_aliases(bank)
    VERSIONES = sorted({v for _, v in aliases.values()})
    if aliases:
        for v in VERSIONES:
            ks = [k for k, (_, vv) in aliases.items() if vv == v]
            print(f"redacciones : {v} · {len(ks)} opciones con texto nuevo aceptado "
                  f"en {len({q for q, _ in ks})} ítems")
    administered = None
    if ADMIN_IDS and os.path.exists(ADMIN_IDS):
        administered = {l.strip() for l in io.open(ADMIN_IDS, encoding="utf-8") if l.strip()}
    print(f"bank         : {len(bank)} questions  [huella verificada]")
    if administered is not None:
        print(f"administered : {len(administered)} of them "
              f"({len(bank) - len(administered)} intentionally not asked)")
    else:
        print(f"administered : los {len(bank)} — sin subset")

    with io.open(export_path, encoding="utf-8") as f:
        export = list(csv.reader(f))
    if not export:
        print("export is empty"); return 1
    header, data = export[0], export[1:]
    print(f"export : {len(data)} responses, {len(header)} columns\n")

    # map export column index -> question_id  (y, aparte, las META)
    col_for_qid, col_for_meta, unmatched = {}, {}, []
    for i, h in enumerate(header):
        m = QID_RE.match(h)
        if m:
            col_for_qid[m.group(1)] = i
            continue
        m = META_RE.match(h)
        if m:
            col_for_meta[m.group(1)] = i
            continue
        unmatched.append(h)

    code_col = next((i for i, h in enumerate(header)
                     if h.strip().upper().startswith("CODIGO")), None)

    # ---------- integrity checks ----------
    problems = []

    expected = administered if administered is not None else set(bank)
    missing = [q for q in expected if q not in col_for_qid]
    unexpected_present = [q for q in col_for_qid
                          if administered is not None and q not in administered]
    extra = [q for q in col_for_qid if q not in bank]
    if missing:
        problems.append(f"{len(missing)} ADMINISTERED questions have no export column "
                        f"(first: {missing[:5]}) — the form and the subset disagree")
    if unexpected_present:
        problems.append(f"{len(unexpected_present)} questions appear in the export but are "
                        f"not in the administered subset: {unexpected_present[:5]}. The form "
                        f"was probably built from the full bank instead of the subset.")
    if extra:
        problems.append(f"{len(extra)} export columns reference unknown ids: {extra[:5]}")
    if code_col is None:
        problems.append("no CODIGO column found — responses cannot be linked to interviews")

    print("unmatched columns (expected: timestamp, CONSENT, CODIGO):")
    for h in unmatched:
        print(f"   - {h[:70]}")
    print()

    # answer-text validation: every recorded answer must exist verbatim in the bank
    bad_answers = collections.Counter()
    rows_out = []
    fix_txt, fix_ts = cargar_fixes()
    excluidos = cargar_exclusiones()
    usados, codigos_raros = set(), []
    versiones = []
    descartadas = []
    for row in data:
        # Normalización: el formulario valida con \s*[Rr]\d{3}\s*, o sea que puede
        # llegar con espacios al borde o con la R en minúscula. Eso se arregla acá y
        # no se reporta: es ruido de tipeo, no un error del respondente.
        crudo = (row[code_col].strip().upper() if code_col is not None
                 and code_col < len(row) else "")
        cod = crudo
        ts = row[0].strip() if row else ""
        for clave, f in fix_txt:
            if crudo.casefold() == clave:
                cod = f["codigo"]; usados.add(id(f))
                print(f"CORRECCIÓN DE CÓDIGO: {crudo!r} -> {cod}  ({f.get('motivo','')})")
                break
        else:
            for clave, f in fix_ts:
                if ts == clave:
                    usados.add(id(f))
                    if f.get("accion") == "descartar":
                        # Fila apartada a propósito (p. ej. un código duplicado de alguien que
                        # todavía no se identificó). No se borra del export: se omite acá, se
                        # anuncia, y en cuanto se sepa quién fue se cambia por un "codigo".
                        cod = None
                        print(f"FILA DESCARTADA por timestamp {ts} (código escrito: {crudo!r})  "
                              f"({f.get('motivo','')})")
                    else:
                        cod = f["codigo"]
                        print(f"CORRECCIÓN DE CÓDIGO por timestamp {ts} -> {cod}  "
                              f"({f.get('motivo','')})")
                    break
        if cod is None:
            descartadas.append(crudo)
            continue
        if cod in excluidos:
            print(f"EXCLUIDO: {cod}  ({excluidos[cod].get('motivo','')})")
            descartadas.append(cod)
            continue
        if cod and not CODE_RE.match(cod):
            codigos_raros.append(crudo)
        rec = {"respondent_id": cod}
        viejo_v = collections.Counter(); nuevo_v = collections.Counter()
        for mid, colname in META_COLS.items():
            ci = col_for_meta.get(mid)
            rec[colname] = (row[ci].strip() if ci is not None and ci < len(row) else "")
        for qid, opts in bank.items():
            ci = col_for_qid.get(qid)
            val = row[ci].strip() if ci is not None and ci < len(row) else ""
            if not val:
                rec[qid] = NOT_ASKED
                continue
            idx = next((k + 1 for k, o in enumerate(opts)
                        if o["option_text"].strip() == val), None)
            if idx is not None and (qid, idx) in aliases:
                viejo_v[aliases[(qid, idx)][1]] += 1   # opción cambiada, respondida con el texto viejo
            if idx is None:
                idx = next((k for (q, k), (t, _) in aliases.items() if q == qid and t == val), None)
                if idx is not None:
                    nuevo_v[aliases[(qid, idx)][1]] += 1   # la misma opción, con el texto nuevo
            if idx is None:
                bad_answers[qid] += 1
                rec[qid] = NOT_ASKED
            else:
                rec[qid] = idx
        rows_out.append(rec)
        # Estado por versión: cada ronda de cambios se cargó en otra fecha, así que se mira por
        # separado. «nuevo» = respondió esa ronda con los textos nuevos.
        v = {"respondent_id": cod}
        for ver in VERSIONES:
            o, n = viejo_v[ver], nuevo_v[ver]
            v[ver] = "mixta" if o and n else "viejo" if o else "nuevo" if n else "indeterminada"
            v[f"{ver}_viejo"], v[f"{ver}_nuevo"] = o, n
        estados = [v[ver] for ver in VERSIONES]
        ultima = next((ver for ver in reversed(VERSIONES) if v[ver] == "nuevo"), None)
        v["version_banco"] = ("mixta" if "mixta" in estados else ultima if ultima else
                              "v4.1" if "viejo" in estados else "indeterminada")
        versiones.append(v)

    if bad_answers:
        problems.append(
            f"{sum(bad_answers.values())} answers did not match any option text "
            f"(worst: {bad_answers.most_common(3)}). Usually means the form was built "
            f"from a different bank version, or the CSV was re-saved by Excel.")

    if codigos_raros:
        problems.append(
            f"{len(codigos_raros)} respuesta(s) con un CODIGO que no tiene forma R###: "
            f"{codigos_raros}. Agregá la corrección en code_fixes.json — NO edites el "
            f"export: se vuelve a bajar y la edición se pierde.")
    sin_usar = [f for _, f in (fix_txt + fix_ts) if id(f) not in usados]
    if sin_usar:
        print("Correcciones declaradas que no matchearon ninguna fila "
              f"(¿entradas viejas?): {[f.get('codigo') or f.get('accion') for f in sin_usar]}\n")
    if descartadas:
        print(f"{len(descartadas)} fila(s) descartada(s) a propósito (ver code_fixes.json): "
              f"{descartadas}\n")

    # blank respondent ids / duplicates
    ids = [r["respondent_id"] for r in rows_out]
    if any(not i for i in ids):
        problems.append(f"{sum(1 for i in ids if not i)} response(s) with no CODIGO")
    dupes = [i for i, n in collections.Counter(i for i in ids if i).items() if n > 1]
    if dupes:
        problems.append(f"duplicate CODIGO values: {dupes} — same person submitted twice?")

    # completeness per respondent
    print("completeness per respondent:")
    for r in rows_out:
        answered = sum(1 for q in expected if r[q] != NOT_ASKED)
        flag = "" if answered == len(expected) else "   <-- INCOMPLETE"
        print(f"   {r['respondent_id'] or '(sin código)':16} {answered}/{len(expected)}{flag}")
    print()

    missing_meta = [m for m in META_COLS if m not in col_for_meta]
    if missing_meta:
        problems.append(
            f"faltan las covariables {missing_meta} en el export. Sin ellas no se puede "
            f"reportar la precisión partida por familiaridad, que es la única razón por "
            f"la que esas preguntas existen. ¿El form se construyó antes de agregarlas?")
    else:
        for mid, colname in sorted(META_COLS.items()):
            seen = {r[colname] for r in rows_out if r[colname]}
            drift = seen - META_EXPECTED[mid]
            if drift:
                problems.append(
                    f"{mid} trae valores que el script no conoce: {sorted(drift)}. "
                    f"El formulario y META_EXPECTED se separaron — si es una variante de "
                    f"redacción de un valor esperado, el corte por familiaridad queda "
                    f"partido en dos buckets. Alineá los dos textos antes de analizar.")
        fam = collections.Counter(r["meta_familiaridad"] for r in rows_out)
        print("familiaridad con el Eneagrama:")
        for k, v in fam.most_common():
            print(f"   {k or '(en blanco)':22} {v}")
        print()

    # ---------- write ----------
    fields = (["respondent_id"] + [META_COLS[m] for m in sorted(META_COLS)]
              + list(bank.keys()))
    with io.open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows_out)

    print(f"wrote {out_path}: {len(rows_out)} rows x {len(fields)} cols")

    if aliases:
        vpath = os.path.join(os.path.dirname(os.path.abspath(out_path)), "responses_version.csv")
        with io.open(vpath, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["respondent_id", "version_banco"] +
                               [c for ver in VERSIONES for c in (ver, f"{ver}_viejo", f"{ver}_nuevo")])
            w.writeheader()
            w.writerows(versiones)
        cnt = collections.Counter(v["version_banco"] for v in versiones)
        print(f"wrote {vpath}: " + " · ".join(f"{k} {n}" for k, n in sorted(cnt.items())))
        mixtas = [v["respondent_id"] for v in versiones if v["version_banco"] == "mixta"]
        if mixtas:
            print(f"   mixtas (retomaron un borrador a mitad del cambio): {mixtas}")
    print("\nNOTE: this file has no labels yet. Join it to the expert-typing sheet on "
          "respondent_id, then derive each respondent's group per conjunto through the "
          "canonical table in config.py. Keep respondent_id — it is the grouping key for "
          "GroupKFold, without which reported accuracy is meaningless.\n")

    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("  x " + p)
        return 1
    print("PASS — export maps cleanly onto the locked bank.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
