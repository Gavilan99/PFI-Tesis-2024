# -*- coding: utf-8 -*-
"""Verificación del supuesto de la reescritura a mitad de recolección (PDR, Consequences).

    python verificar_redaccion.py responses_wide.csv

Compara respondentes VIEJOS (v4.1) contra NUEVOS (v4.1.2) por ronda de cambios, con los ítems no
cambiados como control:
  1. Distribución: χ² respuesta × versión por ítem, p por permutación de la versión entre personas.
     Global: χ² medio de los ítems cambiados menos el de los no cambiados.
  2. Dirección: V de Cramér corregido de cada ítem con el grupo de la persona en el conjunto del ítem,
     calculado por separado en viejos y nuevos. ΔV = V_nuevo − V_viejo. Con pocos nuevos ΔV es ruidoso
     y sesgado; por eso se compara contra el ΔV de los ítems de control, que sufre el mismo sesgo.
     Global: ΔV medio de los cambiados menos el de los no cambiados, p por permutación de la versión.
  3. Composición de tipos de viejos y nuevos.
Las personas `mixta` (si las hay) se excluyen y se informan. Sin group_label: la etiqueta es el grupo
de la PERSONA, la respuesta es la posición elegida.
"""
import os, sys, json, collections
import numpy as np, pandas as pd

import contrast as C
from eda_pilot import cargar
from eda_extra2 import v_cramer

HERE = C.DATA   # datos y salidas, fuera del repositorio (ver README)
N_PERM = 2000
rng = np.random.default_rng(1)


def chi2(r, g):
    _, ri = np.unique(r, return_inverse=True); _, gi = np.unique(g, return_inverse=True)
    t = np.bincount(ri * (gi.max() + 1) + gi, minlength=(ri.max() + 1) * (gi.max() + 1)
                    ).reshape(ri.max() + 1, gi.max() + 1).astype(float)
    t = t[t.sum(1) > 0][:, t.sum(0) > 0]
    e = t.sum(1, keepdims=True) * t.sum(0, keepdims=True) / t.sum()
    return ((t - e) ** 2 / e).sum(), t.shape


def V(r, g):
    x, (a, b) = chi2(r, g)
    return v_cramer(x, len(r), a, b) if min(a, b) > 1 else 0.0


def stats(X, Yc, nuevo, items):
    """Por ítem: χ² de distribución contra la versión, y ΔV de asociación con la etiqueta."""
    d, dv = [], []
    for q, yc in zip(items, Yc):
        d.append(chi2(X[q].values, nuevo)[0])
        dv.append(V(X[q].values[nuevo], yc[nuevo]) - V(X[q].values[~nuevo], yc[~nuevo]))
    return np.array(d), np.array(dv)


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    bank, X, tipos, Y, fmt = cargar(sys.argv[1])
    ver = pd.read_csv(os.path.join(HERE, "responses_version.csv"), dtype=str).set_index("respondent_id")
    vb = ver.version_banco.reindex(X.index)
    mixtas = [c for c in X.index if vb[c] not in ("v4.1", "v4.1.2")]
    if mixtas:
        print(f"excluidas por versión no pura: {mixtas}")
    keep = [c for c in X.index if c not in mixtas]
    X, tipos, Y, vb = X.loc[keep], tipos.loc[keep], Y.loc[keep], vb.loc[keep]
    nuevo = (vb == "v4.1.2").values
    print(f"viejos (v4.1) {int((~nuevo).sum())} · nuevos (v4.1.2) {int(nuevo.sum())}")
    print("composición · viejos: " + " · ".join(f"{t}×{n}" for t, n in sorted(tipos[~nuevo].value_counts().items())))
    print("              nuevos: " + " · ".join(f"{t}×{n}" for t, n in sorted(tipos[nuevo].value_counts().items())))

    al = json.load(open(os.path.join(C.BANK_DIR, "bank_aliases.json"), encoding="utf-8"))["cambios"]
    ronda = collections.defaultdict(set); campos = collections.defaultdict(set)
    for c in al:
        ronda[c["version"]].add(c["question_id"]); campos[c["question_id"]].add(c["campo"])
    items = list(X.columns)
    cambiados = set().union(*ronda.values())
    control = [q for q in items if q not in cambiados]
    Yc = [Y[C.CORTO[bank[q][0]["grouping_system"]]].values for q in items]

    d0, dv0 = stats(X, Yc, nuevo, items)
    nd, ndv = np.zeros((N_PERM, len(items))), np.zeros((N_PERM, len(items)))
    for b in range(N_PERM):
        nd[b], ndv[b] = stats(X, Yc, rng.permutation(nuevo), items)
    p_item = ((nd >= d0).sum(0) + 1) / (N_PERM + 1)
    ix = {q: i for i, q in enumerate(items)}
    ic = [ix[q] for q in control]

    print(f"\ncontrol: {len(control)} ítems no cambiados · ítems con distribución distinta (p<.05): "
          f"{int((p_item[ic] < .05).sum())}/{len(ic)} ({(p_item[ic] < .05).mean():.0%}; azar 5%)")
    print(f"         ΔV medio {dv0[ic].mean():+.3f} · percentiles 10/50/90 del ΔV: "
          + " / ".join(f"{np.percentile(dv0[ic], k):+.3f}" for k in (10, 50, 90)))
    for v in sorted(ronda):
        qs = [q for q in items if q in ronda[v]]
        iq = [ix[q] for q in qs]
        g_d = (d0[iq].mean() - d0[ic].mean()); n_d = nd[:, iq].mean(1) - nd[:, ic].mean(1)
        g_v = (dv0[iq].mean() - dv0[ic].mean()); n_v = ndv[:, iq].mean(1) - ndv[:, ic].mean(1)
        print(f"\n== ronda {v} · {len(qs)} ítems cambiados")
        print(f"   distribución: p<.05 en {int((p_item[iq] < .05).sum())}/{len(iq)} · χ² medio cambiados − control "
              f"{g_d:+.2f} · p = {((n_d >= g_d).sum() + 1) / (N_PERM + 1):.3f}")
        print(f"   asociación:   ΔV medio {dv0[iq].mean():+.3f} vs control {dv0[ic].mean():+.3f} · diferencia {g_v:+.3f} · "
              f"p (sube) = {((n_v >= g_v).sum() + 1) / (N_PERM + 1):.3f} · p (baja) = {((n_v <= g_v).sum() + 1) / (N_PERM + 1):.3f}")
        print("   ítem  formato   cambia                      p distr   V viejo  V nuevo   ΔV   percentil ΔV en control")
        for q in qs:
            i = ix[q]
            vo = V(X[q].values[~nuevo], Yc[i][~nuevo]); vn = V(X[q].values[nuevo], Yc[i][nuevo])
            pc = (dv0[ic] < dv0[i]).mean()
            marca = " ◄" if p_item[i] < .05 else ""
            print(f"   {q}  {fmt[q]:8}  {','.join(sorted(campos[q])):26}  {p_item[i]:.3f}{marca:2}  {vo:7.3f}  {vn:7.3f}  "
                  f"{dv0[i]:+.3f}   {pc:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
