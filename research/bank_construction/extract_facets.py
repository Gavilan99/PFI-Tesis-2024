# -*- coding: utf-8 -*-
"""Extrae la columna `Faceta` de los specs y la deja en facets.json.

POR QUÉ EXISTE
--------------
Dos chequeos de la pasada de consolidación quedaron bloqueados por datos:
  C3  la terna de facetas de un ítem tiene que ser única dentro del conjunto
  C4  la opción no puede contener la etiqueta de su propia faceta
Ninguna estructura del banco sabía qué faceta tiene cada opción: las facetas
viven en tablas markdown de los specs. Esto las transcribe, y marca con
`inferida` todo lo que no salga de un spec declarado — la cohorte v4.1 no tiene
spec, así que sus facetas hay que deducirlas del inventario del memo, y la
diferencia importa cuando se cuenten distribuciones.
"""
import re, io, os, json, collections

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (archivo, grupos, prefijo de nota, offset de fila -> nº de ítem)
SCENARIO = [
 ("Prompt para ChatGPT — Redacción ciega del lote 1 (Centros).md",
  ["Cuerpo","Corazón","Mente"], "lote1", 0),
 # OJO: el archivo titulado "Centros lote 2" contiene en realidad los dominios
 # del LOTE 1, numerados 1-12. Los de centros3 (19-24) están en el spec mixto.
 ("Spec de Facetas — Centros lote 2 (v2, post-revisión).md",
  ["Cuerpo","Corazón","Mente"], "lote1", 0),
 ("Spec de Lote Mixto — v4, post-auditoría del rediseño.md",
  ["Cuerpo","Corazón","Mente"], "centros3", 0),
 ("Spec de Lote Mixto — v4, post-auditoría del rediseño.md",
  ["Asertiva","Complaciente","Retraída"], "hornev2", 0),
 ("Spec de Conjunto — Horneviano (v2, post-revisión).md",
  ["Asertiva","Complaciente","Retraída"], "hornev1", 0),
 ("Spec de Conjunto — Horneviano (v3, final).md",
  ["Asertiva","Complaciente","Retraída"], "hornev1", 0),
 ("Spec de Conjunto — Armónico (v3, correcciones de lenguaje).md",
  ["Positiva","Competente","Reactiva"], "arm", 0),
 ("Spec de Conjunto — Relaciones Objetales (v2, post-auditoría).md",
  ["Apego","Frustración","Rechazo"], "rel", 0),
]

LIKERT = [
 ("Spec de Ítems Likert — Centros lote 1 (v2, post-revisión).md", "likert1"),
 ("Spec de Ítems Likert — Horneviano (v1, reescrito).md", "hlik"),
 ("Spec de Ítems Likert — Armónico (v2, post-auditoría).md", "alik"),
 ("Spec de Ítems Likert — Relaciones Objetales (v2, post-auditoría).md", "rlik"),
]


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _clean(s):
    return re.sub(r"\*+", "", s).split("·")[0].strip()


def scan_tables(path):
    """Devuelve [(encabezados, [filas])] de cada tabla markdown del archivo."""
    out, cur, hdr = [], None, None
    for line in io.open(path, encoding="utf-8"):
        if line.startswith("|"):
            cells = _cells(line)
            if all(set(c) <= set("-: ") for c in cells) and cur is None and hdr:
                cur = []
                continue
            if cur is None:
                hdr = cells
            else:
                cur.append(cells)
        else:
            if cur:
                out.append((hdr, cur))
            cur, hdr = None, None
    if cur:
        out.append((hdr, cur))
    return out


# Los módulos numeran por lote (rel1/rel2, arm1/arm2) y los specs por conjunto
# (rel 1-18, arm 1-18). El alias traduce; se aplica al consultar, no al extraer.
ALIAS = {"rel1": "rel", "rel2": "rel", "arm1": "arm", "arm2": "arm"}


def lookup(note, facets):
    """note tal como está en el módulo -> entrada de facets.json, o None."""
    m = re.match(r"([a-z0-9]+)\s+(\d+)([di])?$", (note or "").split("·")[0].strip())
    if not m:
        return None
    tag = ALIAS.get(m.group(1), m.group(1))
    return facets.get(f"{tag} {int(m.group(2)):02d}")


def main():
    facets, sources = {}, {}
    for fn, groups, tag, off in SCENARIO:
        p = os.path.join(VAULT, fn)
        if not os.path.exists(p):
            print("  FALTA:", fn); continue
        got = 0
        for hdr, rows in scan_tables(p):
            idx = {}
            for g in groups:
                for j, c in enumerate(hdr):
                    if _clean(c) == g:
                        idx[g] = j; break
            if len(idx) < len(groups) or _clean(hdr[0]) != "#":
                continue
            for cells in rows:
                m = re.match(r"\*{0,2}(\d+)", cells[0])
                if not m or len(cells) <= max(idx.values()):
                    continue
                n = int(m.group(1)) + off
                key = f"{tag} {n:02d}"
                facets[key] = {g: _clean(cells[idx[g]]) for g in groups}
                sources[key] = os.path.basename(fn)
                got += 1
        print(f"  {os.path.basename(fn)[:56]:56} {got:3d} filas")

    for fn, tag in LIKERT:
        p = os.path.join(VAULT, fn)
        if not os.path.exists(p):
            print("  FALTA:", fn); continue
        got = 0
        for hdr, rows in scan_tables(p):
            if _clean(hdr[0]) != "#" or "Faceta" not in [_clean(c) for c in hdr]:
                continue
            fi = [_clean(c) for c in hdr].index("Faceta")
            for cells in rows:
                m = re.match(r"\*{0,2}(\d+)", cells[0])
                if not m or len(cells) <= fi:
                    continue
                key = f"{tag} {int(m.group(1)):02d}"
                facets[key] = {"_likert": _clean(cells[fi])}
                sources[key] = os.path.basename(fn)
                got += 1
        print(f"  {os.path.basename(fn)[:56]:56} {got:3d} filas")

    # --- cohorte v4.1: facetas INFERIDAS, no declaradas ---------------------
    # Los 24 ítems de v4.1 son anteriores a los specs y no tienen tabla de
    # facetas. Se infirieron leyendo cada opción contra el inventario del memo
    # de su conjunto, y el revisor aprobó las 72 por escrito (2026-09-17).
    # Se marcan aparte porque una faceta deducida DESDE la opción se nombra a sí
    # misma por construcción: C4 no puede correr sobre ellas sin ser circular.
    inferred = []
    v41p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "facets_v41.json")
    if os.path.exists(v41p):
        v41 = json.loads(io.open(v41p, encoding="utf-8").read())["facets"]
        for key, tri in v41.items():
            facets[key] = tri
            sources[key] = "inferida del memo — aprobada 2026-09-17"
            inferred.append(key)
        print(f"  {'facets_v41.json (INFERIDAS)':56} {len(v41):3d} ítems")

    io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "facets.json"),
            "w", encoding="utf-8").write(
        json.dumps({"facets": facets, "sources": sources,
                    "inferred": sorted(inferred)},
                   ensure_ascii=False, indent=1, sort_keys=True))
    print(f"\n  total claves: {len(facets)}")


if __name__ == "__main__":
    main()
