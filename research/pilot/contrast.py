# -*- coding: utf-8 -*-
"""Contrasta las respuestas contra la tipificación experta, por respondente y agregado.

    python3 contrast.py responses_wide.csv

Une `responses_wide.csv` con el archivo B por `codigo`. Para cada conjunto compara:
  · escenarios — el grupo modal elegido contra el grupo que le toca al tipo
  · Likert     — el grupo con mayor acuerdo medio (inversos dados vuelta)

ESTRATIFICA, NO OMITE
---------------------
Las 39 tipificaciones se apoyan en conocimiento previo del equipo, con entrevista
completa, abreviada o sin entrevista. Eso no las invalida: las hace **de distinta
procedencia**. El script las incluye a todas y corta el agregado por `origen_tipo`,
porque *la precisión según de dónde vino la etiqueta es un resultado en sí mismo*.
Una versión anterior omitía las filas sin entrevista; eso escondía el corte en vez
de medirlo.

También corta por `meta_familiaridad`: si el rendimiento es mucho mayor entre quienes
conocen el Eneagrama, el modelo lee autopercepción y no motivación.

Y reporta la **convergencia 4/4** sobre las filas que tengan los cuatro juicios
triádicos cargados (`grupo_*`). Al azar eso ocurre el 11% de las veces — ver
"NureonAI · Protocolo de tipificación experta" §3.

LÍMITE QUE NO RESUELVE EL CÓDIGO: donde el entrevistador tipificó con el prior a la
vista, la etiqueta no es independiente de él. El script marca cuándo coinciden; no
puede saber si coinciden porque el prior era bueno o porque ancló.
"""
import csv, sys, io, os, collections

GRUPOS = {
    "Centros de Inteligencia": {"Cuerpo": (8, 9, 1), "Corazón": (2, 3, 4), "Mente": (5, 6, 7)},
    "Conjunto Horneviano": {"Asertiva": (3, 7, 8), "Complaciente": (1, 2, 6), "Retraída": (4, 5, 9)},
    "Conjunto Armónico": {"Positiva": (2, 7, 9), "Competente": (1, 3, 5), "Reactiva": (4, 6, 8)},
    "Conjunto de Relaciones Objetales": {"Apego": (3, 6, 9), "Frustración": (1, 4, 7), "Rechazo": (2, 5, 8)},
}
CORTO = {"Centros de Inteligencia": "Centros", "Conjunto Horneviano": "Horneviano",
         "Conjunto Armónico": "Armónico", "Conjunto de Relaciones Objetales": "Relaciones"}
COL_GRUPO = {"Centros de Inteligencia": "grupo_centros",
             "Conjunto Horneviano": "grupo_horneviano",
             "Conjunto Armónico": "grupo_armonico",
             "Conjunto de Relaciones Objetales": "grupo_relaciones"}
NOT_ASKED = "NO_PREGUNTADO"
HERE = os.path.dirname(os.path.abspath(__file__))
# Datos privados (respuestas, planillas de tipificación, listas de exclusión y salidas):
# viven FUERA del repositorio, en la carpeta de NUREON_DATA (por defecto, ./data, ignorada por git).
DATA = os.environ.get("NUREON_DATA", os.path.join(HERE, "data"))
PROJ = DATA
BANK_DIR = os.path.join(os.path.dirname(HERE), "bank")


def leer_lista(nombre):
    """Lista privada de códigos (uno por línea, # para comentarios) en la carpeta de datos."""
    p = os.path.join(DATA, nombre)
    if not os.path.exists(p):
        return set()
    return {l.split("#")[0].strip() for l in io.open(p, encoding="utf-8") if l.split("#")[0].strip()}


# Respondentes que se apartan de los descriptivos y que el entrenamiento reporta con y sin ellos.
# La lista y su motivo son privados: viven en la carpeta de datos, no en el código.
EXCLUIDOS = leer_lista("excluidos.txt")


def grupo_de(tipo, conj):
    return next(g for g, ts in GRUPOS[conj].items() if tipo in ts)


def cargar_b():
    """Lee el archivo B POR NOMBRE DE ENCABEZADO — la planilla se edita a mano y las
    columnas se mueven; leer por índice se rompe en silencio."""
    from openpyxl import load_workbook
    ws = load_workbook(os.path.join(PROJ, "Piloto B - Tipificaciones.xlsx"))["Tipificaciones"]
    hdr = {}
    for c in range(1, ws.max_column + 1):
        v = ws.cell(row=1, column=c).value
        if v:
            hdr[str(v).strip()] = c
    out = {}
    for r in range(3, ws.max_row + 1):
        cod = ws.cell(row=r, column=1).value
        if not (isinstance(cod, str) and cod.startswith("R")):
            continue
        out[cod] = {k: ws.cell(row=r, column=c).value for k, c in hdr.items()}
    return out


def cargar_prior():
    from openpyxl import load_workbook
    p = os.path.join(PROJ, "Piloto C - Prior (sellado).xlsx")
    if not os.path.exists(p):
        return {}
    ws = load_workbook(p)["Prior"]
    return {ws.cell(row=r, column=1).value: ws.cell(row=r, column=2).value
            for r in range(3, ws.max_row + 1) if ws.cell(row=r, column=1).value}


def cargar_banco():
    bank = collections.defaultdict(list)
    for r in csv.DictReader(io.open(os.path.join(BANK_DIR, "NureonAI Prototype v4.1.csv"), encoding="utf-8")):
        bank[r["question_id"]].append(r)
    for q in bank:
        bank[q].sort(key=lambda r: int(r["display_order"]))
    return bank


def perfil(resp, bank, conj, fmt):
    if fmt == "scenario":
        picks = []
        for q, opts in bank.items():
            if opts[0]["grouping_system"] != conj or opts[0]["format"] != "scenario":
                continue
            v = resp.get(q)
            if v and v != NOT_ASKED:
                picks.append(opts[int(v) - 1]["group_label"])
        c = collections.Counter(picks)
        return {g: c.get(g, 0) for g in GRUPOS[conj]}, len(picks)
    vals = collections.defaultdict(list)
    for q, opts in bank.items():
        if opts[0]["grouping_system"] != conj or opts[0]["format"] != "likert":
            continue
        v = resp.get(q)
        if not v or v == NOT_ASKED:
            continue
        x = int(v)
        if (opts[0].get("polarity") or "").strip().lower().startswith("inv"):
            x = 6 - x
        vals[opts[0]["group_label"]].append(x)
    return ({g: sum(v) / len(v) for g, v in vals.items()},
            sum(len(v) for v in vals.values()))


def evaluar(resp, bank, tipo):
    """Devuelve [(conjunto, formato, acierto_estricto, empate, esperado, top, valor, n)]."""
    out = []
    for conj in GRUPOS:
        esp = grupo_de(tipo, conj)
        for fmt, et in (("scenario", "esc"), ("likert", "lik")):
            d, n = perfil(resp, bank, conj, fmt)
            if not d or not n:
                continue
            top = max(d, key=lambda g: d[g])
            empate = sum(1 for g in d if d[g] == d[top]) > 1
            ok = d.get(esp, -1) == d[top]
            out.append((CORTO[conj], et, ok and not empate, ok and empate, esp, top, d.get(esp, 0), n))
    return out


def tabla(titulo, celdas):
    """celdas: {(conjunto, et): [aciertos, total]}"""
    print(f"\n{titulo}")
    print(f"  {'':12} {'escenario':>11} {'likert':>11}")
    ta = tt = 0
    for conj in CORTO.values():
        fila = []
        for et in ("esc", "lik"):
            a, t = celdas.get((conj, et), [0, 0])
            ta += a; tt += t
            fila.append(f"{a}/{t}" if t else "—")
        print(f"  {conj:12} {fila[0]:>11} {fila[1]:>11}")
    print(f"  {'TOTAL':12} {f'{ta}/{tt}':>11} {f'({ta/tt:.0%})' if tt else '':>11}")
    return ta, tt


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); return 2
    bank, B, prior = cargar_banco(), cargar_b(), cargar_prior()
    respuestas = {r["respondent_id"]: r for r in csv.DictReader(io.open(args[0], encoding="utf-8"))}

    usables = [c for c in respuestas if B.get(c) and B[c].get("tipo_asignado")]
    sin_tipo = sorted(set(respuestas) - set(usables))
    if sin_tipo:
        print(f"Sin tipo en B: {sin_tipo}\n")
    if not usables:
        print("Ninguna fila usable."); return 1

    todo = collections.defaultdict(lambda: [0, 0])
    por_origen = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    por_fam = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    sin_excluidos = collections.defaultdict(lambda: [0, 0])
    conv = []

    for cod in sorted(usables):
        b, resp = B[cod], respuestas[cod]
        tipo = int(b["tipo_asignado"])
        origen = (b.get("origen_tipo") or "sin declarar").strip()
        fam = (resp.get("meta_familiaridad") or "sin dato").strip()
        alerta = " [tipo == prior]" if prior.get(cod) == b["tipo_asignado"] else ""
        print(f"── {cod} · tipo {tipo} · {origen} · confianza {b.get('confianza')}{alerta}")
        print(f"   familiaridad {fam} · autopercibido {resp.get('meta_tipo_autopercibido','?')}"
              f" · adivinó {resp.get('meta_intento_adivinar','?')}")

        filas = collections.defaultdict(list)
        for conj, et, ok, emp, esp, top, val, n in evaluar(resp, bank, tipo):
            for acc in (todo, por_origen[origen], por_fam[fam]):
                acc[(conj, et)][0] += ok; acc[(conj, et)][1] += 1
            if cod not in EXCLUIDOS:
                sin_excluidos[(conj, et)][0] += ok; sin_excluidos[(conj, et)][1] += 1
            marca = "ok " if ok else ("=  " if emp else "X  ")
            v = f"{val:.0f}/{n}" if et == "esc" else f"{val:.2f}"
            filas[conj].append(f"{et} {marca}{esp} {v} (top: {top})")
        for conj in CORTO.values():
            if filas[conj]:
                print(f"   {conj:11} " + " | ".join(filas[conj]))

        # convergencia 4/4 de los juicios triádicos, si están cargados
        juicios = {c: b.get(COL_GRUPO[c]) for c in GRUPOS}
        if all(juicios.values()):
            cand = set(range(1, 10))
            for c, g in juicios.items():
                cand &= set(GRUPOS[c][str(g).strip()])
            conv.append((cod, len(cand) == 1 and tipo in cand))
        print()

    print("=" * 66)
    ta, tt = tabla(f"AGREGADO — {len(usables)} respondentes (aciertos estrictos, empate no cuenta)", todo)
    print(f"\n  azar ≈ 33%")

    if any(c in EXCLUIDOS for c in usables):
        tabla("SIN LOS RESPONDENTES DE excluidos.txt", sin_excluidos)

    for etiqueta, grupos in (("POR ORIGEN DE LA ETIQUETA", por_origen),
                             ("POR FAMILIARIDAD CON EL ENEAGRAMA", por_fam)):
        print(f"\n{'-'*66}\n{etiqueta}")
        for k in sorted(grupos):
            a = sum(v[0] for v in grupos[k].values()); t = sum(v[1] for v in grupos[k].values())
            n = sum(1 for c in usables if (
                (B[c].get("origen_tipo") or "sin declarar").strip() == k if grupos is por_origen
                else (respuestas[c].get("meta_familiaridad") or "sin dato").strip() == k))
            print(f"  {k:24} n={n:3}  {a}/{t}  ({a/t:.0%})" if t else f"  {k:24} sin datos")

    print(f"\n{'-'*66}\nCONVERGENCIA DE LOS CUATRO JUICIOS TRIÁDICOS")
    if conv:
        ok = sum(1 for _, c in conv if c)
        print(f"  {ok}/{len(conv)} convergen en el tipo asignado ({ok/len(conv):.0%}) · al azar ≈ 11%")
        malos = [c for c, v in conv if not v]
        if malos:
            print(f"  no convergen: {malos}")
    else:
        print("  sin datos — requiere las columnas grupo_* cargadas en el archivo B")
    return 0


if __name__ == "__main__":
    sys.exit(main())
