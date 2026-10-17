# -*- coding: utf-8 -*-
"""Plan §6 septies: concentración de ancla Likert del tipo 4 (mayor) y del tipo 5 (menor), prospectivo.

    python estilo_prospectivo.py responses_wide.csv

Concentración = fracción de los Likert respondidos que cae en el ancla más usada por la persona
(la misma métrica de `pilot_metrics.py` §6). Se evalúan SÓLO los 4 y los 5 que no están en
`t45_vistos.txt`, contra todas las personas con tipo distinto de la muestra vigente (vistas y nuevas).
Mann-Whitney de una cola por permutación (200 000, semilla 1). Holm sobre los dos tests.
Mínimo de 5 personas nuevas del tipo para que su test cuente; con menos, se reporta sin decidir.

Plan §6 octies (2026-10-14): extremos del tipo 5 (MAYOR que el resto). Extremos = fracción de los
Likert respondidos en 1 o 5. Mismo test y mínimo, pero con su propio congelamiento
(`t5ext_vistos.txt`) y evaluado solo, a .05, fuera del Holm de §6 septies (declarado en el plan).
"""
import csv, io, os, sys, collections, statistics as st
import contrast as C
import pilot_metrics as P

HERE = C.DATA   # datos y salidas, fuera del repositorio (ver README)
VISTOS = os.path.join(HERE, "t45_vistos.txt")
VISTOS_EXT = os.path.join(HERE, "t5ext_vistos.txt")     # §6 octies
HIP = ((4, "mayor"), (5, "menor"))
N_MIN = 5


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    bank, B, _ = P.con_copias()
    R = {r["respondent_id"]: r for r in csv.DictReader(io.open(sys.argv[1], encoding="utf-8"))}
    vistos = {l.strip() for l in open(VISTOS, encoding="utf-8") if l.strip() and not l.startswith("#")}
    use = [c for c in R if c not in P.EXC and B.get(c) and B[c].get("tipo_asignado")]
    T = {c: int(B[c]["tipo_asignado"]) for c in use}
    sin_tipo = [c for c in R if c not in vistos and c not in T and c not in P.EXC]

    def conc(c):
        v = [R[c][q] for q, o in bank.items() if o[0]["format"] == "likert"
             and R[c].get(q) not in (None, "", C.NOT_ASKED)]
        return max(collections.Counter(v).values()) / len(v)

    cc = {c: conc(c) for c in use}
    nuevos = [c for c in use if c not in vistos]
    print(f"muestra con tipo: {len(use)} · nuevas desde el congelamiento: {len(nuevos)}"
          + (f" · nuevas SIN tipo en B (no entran): {sin_tipo}" if sin_tipo else ""))
    res = []
    for t, cola in HIP:
        g = [c for c in nuevos if T[c] == t]
        resto = [cc[c] for c in use if T[c] != t]
        a = [cc[c] for c in g]
        print(f"\n== tipo {t}: concentración {cola} que el resto · nuevos n={len(g)} (mínimo {N_MIN}) · resto n={len(resto)}")
        for c in sorted(g, key=lambda c: -cc[c]):
            print(f"   {c} {cc[c]:.0%}")
        if not a:
            res.append((t, None)); continue
        s = -1 if cola == "menor" else 1
        p = P.perm_u([s * x for x in a], [s * x for x in resto], 1)
        ps = sum((i > j) + .5 * (i == j) for i in a for j in resto) / len(a) / len(resto)
        print(f"   mediana {st.median(a):.0%} vs resto {st.median(resto):.0%} · P({t} > otro) = {ps:.2f} · p una cola = {p:.4f}")
        res.append((t, p if len(a) >= N_MIN else None))
    val = sorted((p, t) for t, p in res if p is not None)
    print("\nHOLM (sólo tests con n nuevos ≥ %d):" % N_MIN)
    if not val:
        print("   ningún test alcanza el mínimo todavía: se reporta sin decidir")
    m, sigue = len(val), True
    for i, (p, t) in enumerate(val):
        ok = sigue and p <= .05 / (m - i)
        sigue = ok
        print(f"   tipo {t}: p = {p:.4f} · umbral {.05 / (m - i):.4f} · {'SE CONFIRMA' if ok else 'no se confirma'}")

    # §6 octies: extremos del 5 (mayor que el resto), con su propio congelamiento y sin Holm conjunto
    vistos8 = {l.strip() for l in open(VISTOS_EXT, encoding="utf-8") if l.strip() and not l.startswith("#")}

    def extremos(c):
        v = [R[c][q] for q, o in bank.items() if o[0]["format"] == "likert"
             and R[c].get(q) not in (None, "", C.NOT_ASKED)]
        return sum(x in ("1", "5") for x in v) / len(v)

    ex = {c: extremos(c) for c in use}
    g = [c for c in use if T[c] == 5 and c not in vistos8]
    resto = [ex[c] for c in use if T[c] != 5]
    print(f"\n== §6 octies · tipo 5: extremos MAYOR que el resto · nuevos n={len(g)} (mínimo {N_MIN}) · resto n={len(resto)}")
    for c in sorted(g, key=lambda c: -ex[c]):
        print(f"   {c} {ex[c]:.0%}")
    if g:
        a = [ex[c] for c in g]
        p = P.perm_u(a, resto, 1)
        ps = sum((i > j) + .5 * (i == j) for i in a for j in resto) / len(a) / len(resto)
        print(f"   mediana {st.median(a):.0%} vs resto {st.median(resto):.0%} · P(5 > otro) = {ps:.2f} · p una cola = {p:.4f}")
        print("   " + ("SE CONFIRMA" if len(g) >= N_MIN and p <= .05 else
                     "no se confirma" if len(g) >= N_MIN else "bajo el mínimo: se reporta sin decidir"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
