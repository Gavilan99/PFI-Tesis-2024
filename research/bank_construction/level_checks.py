# -*- coding: utf-8 -*-
"""
Paso 5 de la pasada de consolidación — CHEQUEOS DE NIVEL sobre el banco entero.

Un defecto de nivel es el que no se ve fila por fila: el ítem está bien solo y mal
en el conjunto. Los tres defectos más caros del proyecto fueron de este tipo
(el meta-esquema del lote mixto, las meta-familias de Relaciones, la afordancia
de Armónico) y los tres eran invisibles leyendo ítem por ítem.

LOS UMBRALES DE ESTE ARCHIVO SE FIJARON ANTES DE CORRER NADA (2026-09-18).
Es la regla del proyecto: un hallazgo que no venga de un chequeo con umbral
fijado de antemano no es un hallazgo, es una hipótesis. Y la segunda regla que
gobierna todo lo de abajo: la unidad correcta de un chequeo léxico es una TASA
sobre la población que podría exhibirlo, nunca un conteo de apariciones.
"""
import collections
import importlib
import io
import itertools
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# UMBRALES — fijados antes de la primera corrida
# ---------------------------------------------------------------------------
N1_CLUSTER_SHARE = 0.33   # una familia de dominios que se lleve 1/3 de un conjunto
N1_STEM_SIM      = 0.25   # Jaccard de contenido para considerar dos dominios parientes
N2_FRAME_SHARE   = 0.40   # un armazón proposicional en 40% de las 24 opciones del grupo
N3_AFFORD_SHARE  = 0.50   # mayoría de anclajes de un grupo favoreciendo su propia operación
N4_FACET_SHARE   = 0.30   # una faceta en 30% de las opciones de un grupo
N4_FACET_RATIO   = 0.50   # un grupo con menos de la mitad de facetas que el máximo del conjunto
# N5: el umbral de 0.50 con el que se corrió primero es DEGENERADO a este n.
# Con 4 ítems y 3 valores distintos, la concentración MÍNIMA posible ya es 2/4 =
# 50%: el chequeo marcaba el mejor reparto alcanzable. Se reemplaza por el mismo
# criterio que arregló C4 — se marca cuando un valor se lleva TODO el grupo, que
# sí es evitable — con piso de n. Es la quinta vez que un umbral de proporción
# falla por no mirar cuál era el mínimo alcanzable; queda escrito como ley:
#   un umbral de concentración sólo dice algo si es mayor que el que produciría
#   el reparto más parejo posible dado n y la cantidad de valores disponibles.
N5_DIM_ALL       = True   # sólo alerta si UN valor cubre el grupo entero
N5_DIM_MIN_N     = 3      # y sólo con al menos 3 anclajes
N6_AXIS_JACCARD  = 0.30   # mismo umbral que C2, ya calibrado
# N8 — dominios parecidos ENTRE conjuntos. Ningún otro chequeo los compara: N1
# agrupa dentro de cada conjunto y check_overlap mira opciones, no stems. Importa
# porque los cuatro conjuntos se administran juntos: si el respondente ve dos
# veces la misma escena con dos juegos de opciones, puede anclar la segunda en la
# primera, y eso es correlación inducida ENTRE conjuntos — exactamente lo que
# amenaza la independencia de los clasificadores.
# Umbral 0.25, heredado de N1 (ya calibrado) y fijado antes de correrlo.
# Se reporta además una franja de VIGILANCIA por debajo del umbral: el anclaje
# mutuo no empieza en 0.25, y el revisor pidió verlos aunque no disparen.
N8_STEM_ALERT    = 0.25
N8_STEM_WATCH    = 0.18
# CORRECCIÓN tras la primera corrida (2026-09-19): descontar la frase portadora
# deja stems de 2-4 palabras de contenido, y ahí UNA palabra compartida ya da
# 0.25. Es la misma ley que obligó a rehacer N5: el umbral no decía nada porque
# no miraba el denominador. Se agrega un piso duro — una palabra compartida es
# una palabra, DOS son una escena — y el umbral de proporción se conserva.
N8_MIN_SHARED    = 2
# La frase portadora ("lo que más te costaría ... sería", "lo primero que se te
# viene es") es común a casi todos los dominios y produce falsos positivos: dos
# de los tres primeros hits sólo compartían eso. Se descuenta antes de comparar.
CARRIER = set("""costaria seria cuesta hacer hacés primero viene sale importa
buscas priorizas tolerarias soportas molesta afecta duele pesa peor""".split())
STOP = set("""para pero como cuando donde porque aunque sobre entre desde hasta
sin con por que los las una unos unas del este esta esto eso ese esa algo todo
toda todos todas mas muy ya sea ser estar tener hacer poder mismo misma otro otra
lo la el en de un y o a se te vos tu tus su sus le les me mi nos si no""".split())


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def content(s):
    return set(w for w in re.findall(r"[a-z]+", norm(s)) if len(w) > 3 and w not in STOP)


def jac(a, b):
    return len(a & b) / len(a | b) if (a | b) else 0.0


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
MODULES = [importlib.import_module(m) for m in
           ("p41_centros", "p41_horneviano", "p41_armonico", "p41_relaciones")]
FJ = json.load(io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "facets.json"), encoding="utf-8"))
FAC, INFERRED = FJ["facets"], set(FJ.get("inferred", []))
ALIAS = {"rel1": "rel", "rel2": "rel", "arm1": "arm", "arm2": "arm"}


def fkey(note):
    n = (note or "").split("·")[0].strip()
    if n in FAC:
        return n
    m = re.match(r"([a-z0-9]+)\s+(\d+)([di])?$", n)
    return f"{ALIAS.get(m.group(1), m.group(1))} {int(m.group(2)):02d}" if m else None


# El campo de opciones tiene tres formas en los módulos: lista de (texto, grupo)
# para escenario, un string con el grupo para Likert directo, y ("Grupo",
# "inversa") para Likert inverso. Se normaliza acá, una vez, a [(texto, grupo)]:
# para Likert el "texto" es la afirmación, que es la que se mide.
def _norm_opts(stem, o):
    if isinstance(o, str):
        return [(stem, o)]
    if isinstance(o, (list, tuple)) and len(o) == 2 and all(isinstance(x, str) for x in o):
        return [(stem, o[0])]          # (grupo, "inversa")
    return [(t, g) for t, g in o]


ITEMS = []   # (system, qid, source, stem, qtype, [(texto, grupo)])
for mod in MODULES:
    for it in mod.ITEMS:
        ITEMS.append((mod.SYSTEM, it[1], it[1].split("·")[0].strip(),
                      it[2], it[3], _norm_opts(it[2], it[4])))
SCEN = [x for x in ITEMS if x[4] == "scenario"]
LIK = [x for x in ITEMS if x[4] == "likert"]
SYSTEMS = [m.SYSTEM for m in MODULES]
GROUPS = {m.SYSTEM: list(m.GROUPS) for m in MODULES}


def opts_of(system, group, qtype="scenario"):
    out = []
    for sysname, src_full, src, stem, qt, opts in ITEMS:
        if sysname != system or qt != qtype:
            continue
        for t, g in opts:
            if g == group:
                out.append((src, stem, t))
    return out


def hdr(n, title):
    print("\n" + "=" * 74)
    print("N%d · %s" % (n, title))
    print("=" * 74)


findings = []


def flag(code, text):
    findings.append((code, text))
    print("   >>> " + text)


# ---------------------------------------------------------------------------
# N1 · Meta-esquema: ¿los dominios de un conjunto se agrupan en familias?
# ---------------------------------------------------------------------------
hdr(1, "Meta-esquema por conjunto — familias de dominios (alerta: familia >= %d%%)"
    % (N1_CLUSTER_SHARE * 100))
for system in SYSTEMS:
    stems = [(src, stem) for s, sf, src, stem, qt, o in ITEMS
             if s == system and qt == "scenario"]
    sets = [content(st) for _, st in stems]
    n = len(stems)
    # clustering de un paso: componentes conexas sobre el grafo de similitud
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, j in itertools.combinations(range(n), 2):
        if jac(sets[i], sets[j]) >= N1_STEM_SIM:
            parent[find(i)] = find(j)
    comp = collections.defaultdict(list)
    for i in range(n):
        comp[find(i)].append(i)
    big = sorted((v for v in comp.values() if len(v) > 1), key=len, reverse=True)
    print("  %-34s %d dominios · %d familias de >1 · mayor = %d (%.0f%%)"
          % (system[:34], n, len(big), len(big[0]) if big else 1,
             100 * (len(big[0]) if big else 1) / n))
    for grp in big:
        share = len(grp) / n
        if share >= N1_CLUSTER_SHARE:
            flag("N1", "%s: familia de dominios con %d de %d (%.0f%%)"
                 % (system, len(grp), n, share * 100))
        if len(grp) >= 3 or share >= N1_CLUSTER_SHARE:
            for i in grp:
                print("        %-10s %s" % (stems[i][0], stems[i][1][:78]))

# ---------------------------------------------------------------------------
# N2 · Armazón proposicional sobre las 24 opciones del grupo
# ---------------------------------------------------------------------------
# build.py corre como script y termina en sys.exit(), así que no se puede
# importar. Se copian sus dos constantes calibradas y la función, verbatim, para
# que N2 use EXACTAMENTE la misma definición de armazón que el chequeo por lote.
# Si cambian en build.py, tienen que cambiar acá — queda anotado en las dos.
FRAME_MARKERS = {"no", "sin", "todavia", "ya", "aun", "aunque", "tampoco",
                 "nunca", "nada"}                         # == build.py:557
FRAME_LEN = 2                                             # == build.py:558


def _frame(text):                                         # == build.py:565
    ws = [w for w in re.findall(r"[a-z]+", norm(text)) if w in FRAME_MARKERS]
    return " ".join(ws[:FRAME_LEN]) if ws else None


hdr(2, "Armazón proposicional por grupo sobre TODAS sus opciones (alerta >= %d%%)"
    % (N2_FRAME_SHARE * 100))
for system in SYSTEMS:
    for g in GROUPS[system]:
        texts = [t for _, _, t in opts_of(system, g)]
        c = collections.Counter(f for f in (_frame(t) for t in texts) if f)
        if not c:
            print("  %-34s %-14s sin armazón detectado" % (system[:34], g))
            continue
        top, k = c.most_common(1)[0]
        share = k / len(texts)
        print("  %-34s %-14s «%s» %d/%d = %.0f%%"
              % (system[:34], g, top, k, len(texts), share * 100))
        if share >= N2_FRAME_SHARE:
            flag("N2", "%s / %s: armazón «%s» en %d de %d (%.0f%%)"
                 % (system, g, top, k, len(texts), share * 100))

# ---------------------------------------------------------------------------
# N3 · Afordancia de los anclajes Likert
# ---------------------------------------------------------------------------
hdr(3, "Afordancia de los anclajes Likert (alerta: > %d%% favorece su propio grupo)"
    % (N3_AFFORD_SHARE * 100))
AFF = {}
try:
    AFF = json.load(io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "afordancia.json"), encoding="utf-8"))
except Exception:
    pass
if not AFF:
    print("  SIN DATOS — la columna Afordancia existe sólo en los specs Likert de")
    print("  Armónico y Relaciones. Correr extract_dims.py para cargarla.")
else:
    by = collections.defaultdict(collections.Counter)
    cov = collections.Counter()
    for system, sf, src, stem, qt, opts in LIK:
        a = AFF.get(src)
        g = opts[0][1]
        cov[system] += 1
        if a:
            by[(system, g)][norm(a)] += 1
    for (system, g), c in sorted(by.items()):
        tot = sum(c.values())
        own = sum(v for k, v in c.items() if k not in ("mixta", "mixto"))
        print("  %-34s %-14s %d anclajes · no-mixta %d (%.0f%%)  %s"
              % (system[:34], g, tot, own, 100 * own / tot, dict(c)))
        if own / tot > N3_AFFORD_SHARE:
            flag("N3", "%s / %s: %d de %d anclajes con afordancia propia (%.0f%%)"
                 % (system, g, own, tot, 100 * own / tot))
    sin = [s for s in SYSTEMS if not any(k[0] == s for k in by)]
    if sin:
        print("  sin columna de afordancia en el spec: " + " · ".join(sin))

# ---------------------------------------------------------------------------
# N4 · Distribución de facetas por grupo (y separando inferidas)
# ---------------------------------------------------------------------------
hdr(4, "Distribución de facetas por grupo (alerta: una faceta >= %d%%, o inventario "
    "< %d%% del mayor del conjunto)" % (N4_FACET_SHARE * 100, N4_FACET_RATIO * 100))
dist = collections.defaultdict(collections.Counter)
inf_n = collections.Counter()
for system, sf, src, stem, qt, opts in ITEMS:
    tri = FAC.get(fkey(src)) or {}
    k = fkey(src)
    for t, g in opts:
        fa = tri.get(g) or tri.get("_likert")
        if fa:
            dist[(system, g)][fa] += 1
            if k in INFERRED:
                inf_n[(system, g)] += 1
for system in SYSTEMS:
    counts = {g: len(dist[(system, g)]) for g in GROUPS[system]}
    mx = max(counts.values())
    for g in GROUPS[system]:
        c = dist[(system, g)]
        tot = sum(c.values())
        top, k = c.most_common(1)[0]
        print("  %-34s %-14s %2d facetas / %2d opciones · top «%s» %d (%.0f%%) · inferidas %d"
              % (system[:34], g, len(c), tot, top, k, 100 * k / tot, inf_n[(system, g)]))
        if k / tot >= N4_FACET_SHARE:
            flag("N4", "%s / %s: faceta «%s» en %d de %d (%.0f%%)"
                 % (system, g, top, k, tot, 100 * k / tot))
        if len(c) / mx < N4_FACET_RATIO:
            flag("N4", "%s / %s: inventario de %d facetas contra %d del mayor del conjunto"
                 % (system, g, len(c), mx))

# ---------------------------------------------------------------------------
# N5 · Balance de las dimensiones del anclaje Likert
# ---------------------------------------------------------------------------
hdr(5, "Balance de dimensiones del anclaje Likert (alerta: un valor cubre el grupo "
    "entero, n >= %d)" % N5_DIM_MIN_N)
DIMS = {}
try:
    DIMS = json.load(io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          "dims.json"), encoding="utf-8"))
except Exception:
    pass
if not DIMS:
    print("  SIN DATOS — correr extract_dims.py")
else:
    bydim = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for system, sf, src, stem, qt, opts in LIK:
        d = DIMS.get(src)
        if not d:
            continue
        g = opts[0][1]
        for dim, val in d.items():
            if dim == "Afordancia":
                continue
            bydim[(system, g)][dim][norm(val)] += 1
    for (system, g), dd in sorted(bydim.items()):
        for dim, c in sorted(dd.items()):
            tot = sum(c.values())
            top, k = c.most_common(1)[0]
            mark = ""
            if k == tot and tot >= N5_DIM_MIN_N:
                mark = "  <-- REVISAR"
                flag("N5", "%s / %s · %s: «%s» en LAS %d de %d — sin variación"
                     % (system, g, dim, top, k, tot))
            print("  %-30s %-13s %-12s %d valores / %d · top «%s» %d%s"
                  % (system[:30], g, dim, len(c), tot, top, k, mark))
    faltan = [s for s in SYSTEMS if not any(x[0] == s for x in bydim)]
    if faltan:
        print("  sin columnas dimensionales en el spec: " + " · ".join(faltan))

# ---------------------------------------------------------------------------
# N8 · Dominios parecidos entre conjuntos
# ---------------------------------------------------------------------------
# Pares ya vistos y aceptados por el revisor (2026-09-19): no se tocan, pero se
# imprimen siempre para que queden identificados como riesgo de anclaje mutuo.
N8_REGISTERED = {("v4.1 C5", "v4.1 H1"): "misma escena en dos conjuntos — registrado, sin tocar",
                 ("v4.1 C3", "v4.1 A3"): "discusión / conflicto en tu familia — registrado, sin tocar",
                 ("hornev2 13", "rel1 05"): "un plan cancelado / un pedido de ayuda — escenas distintas, revisado 2026-09-19",
                 ("hornev1 10", "rel1 09"): "carga propia / tiempo de la pareja — escenas distintas, revisado 2026-09-19"}
hdr(8, "Dominios de conjuntos distintos (alerta >= %.2f · vigilancia >= %.2f, "
    "descontando la frase portadora)" % (N8_STEM_ALERT, N8_STEM_WATCH))
_stems = [(x[0], x[2], x[3]) for x in ITEMS if x[4] == "scenario"]
_pairs = []
for (s1, k1, t1), (s2, k2, t2) in itertools.combinations(_stems, 2):
    if s1 == s2:
        continue
    a, b = content(t1) - CARRIER, content(t2) - CARRIER
    j = jac(a, b)
    if j >= N8_STEM_WATCH and len(a & b) >= N8_MIN_SHARED:
        _pairs.append((j, k1, t1, k2, t2, sorted(a & b)))
print("  %d pares entre conjuntos" % (sum(1 for (s1, _, _), (s2, _, _)
      in itertools.combinations(_stems, 2) if s1 != s2)))
for j, k1, t1, k2, t2, sh in sorted(_pairs, reverse=True):
    reg = N8_REGISTERED.get((k1, k2)) or N8_REGISTERED.get((k2, k1))
    tag = "REGISTRADO" if reg else ("ALERTA" if j >= N8_STEM_ALERT else "vigilancia")
    print("   %.2f  %-11s %-9s %s" % (j, tag, k1, t1[:66]))
    print("                          %-9s %s" % (k2, t2[:66]))
    print("                          comparten: %s%s" % (sh, "  — " + reg if reg else ""))
    if j >= N8_STEM_ALERT and not reg:
        flag("N8", "%s y %s comparten escena entre conjuntos (%.2f)" % (k1, k2, j))
if not _pairs:
    print("   sin pares por encima de la franja de vigilancia")

# ---------------------------------------------------------------------------
# N6 / N7 · Ejes que atraviesan conjuntos
# ---------------------------------------------------------------------------
AXES = [
    ("N6 · eje dependencia", [("Conjunto Horneviano", "Retraída"),
                              ("Conjunto de Relaciones Objetales", "Rechazo"),
                              ("Conjunto de Relaciones Objetales", "Apego")]),
    ("N7 · eje 8-idad", [("Centros de Inteligencia", "Cuerpo"),
                         ("Conjunto Horneviano", "Asertiva"),
                         ("Conjunto Armónico", "Reactiva"),
                         ("Conjunto de Relaciones Objetales", "Rechazo")]),
]
for name, members in AXES:
    hdr(int(name[1]), name[5:] + " — opciones de grupos que pueden colapsar "
        "(alerta Jaccard >= %.2f)" % N6_AXIS_JACCARD)
    pool = []
    for system, g in members:
        for src, stem, t in opts_of(system, g):
            pool.append((system, g, src, t, content(t)))
    print("  %d opciones en el eje (%s)"
          % (len(pool), " · ".join("%s %d" % (g, sum(1 for p in pool if p[1] == g))
                                   for _, g in members)))
    hits = 0
    for a, b in itertools.combinations(pool, 2):
        if a[1] == b[1]:
            continue
        j = jac(a[4], b[4])
        if j >= N6_AXIS_JACCARD:
            hits += 1
            flag(name[:2], "%.2f  %s/%s «%s»  vs  %s/%s «%s»"
                 % (j, a[2], a[1], a[3][:52], b[2], b[1], b[3][:52]))
    if not hits:
        print("   sin pares por encima del umbral")

# ---------------------------------------------------------------------------
print("\n" + "=" * 74)
print("HALLAZGOS: %d" % len(findings))
for c, t in findings:
    print("  [%s] %s" % (c, t))
print("=" * 74)
