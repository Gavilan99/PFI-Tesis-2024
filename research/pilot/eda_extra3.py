# -*- coding: utf-8 -*-
"""Análisis rápidos, tercera tanda (sobre las predicciones ya guardadas y las respuestas).

    python eda_extra3.py responses_wide.csv

  H1 ítems asociados con varias etiquetas: nulo correcto (permutando el TIPO, que arrastra a sus 4
     grupos) y relación con la popularidad de la opción más elegida
  H2 acierto de cada conjunto según el tipo real (predicciones fuera del fold, P_por_persona)
  H3 precisión / recall / F1 por tipo, con y sin los respondentes de excluidos.txt
  H4 sensibilidad de «predicho / real» por tipo: remuestreo de personas (bootstrap)
"""
import os, sys, collections, warnings
import numpy as np, pandas as pd
from scipy.stats import spearmanr

import contrast as C
from eda_pilot import cargar, chi2_bloques
from eda_extra2 import onehot_items, G_of

warnings.filterwarnings("ignore")
HERE = C.DATA   # datos y salidas, fuera del repositorio (ver README)
AOUT = os.path.join(HERE, "analisis_out")
CONJ = list(C.GRUPOS)
rng = np.random.default_rng(1)


def main():
    bank, X, tipos, Y, fmt = cargar(sys.argv[1] if len(sys.argv) > 1 else "responses_wide.csv")
    items = list(X.columns); n = len(X)
    Oh, owners = onehot_items(X, fmt)

    # H1
    print("== H1 · Ítems asociados con 2+ etiquetas — nulo permutando el tipo (arrastra sus 4 grupos)")
    def labs_de(t):
        return {**{C.CORTO[c]: np.array([C.grupo_de(x, c) for x in t]) for c in CONJ}, "tipo": np.asarray(t)}
    obs_labs = labs_de(tipos.values)
    NULL = {k: [] for k in obs_labs}
    for _ in range(1000):
        for k, lab in labs_de(rng.permutation(tipos.values)).items():
            NULL[k].append(chi2_bloques(Oh, owners, G_of(lab)))
    NULL = {k: np.array(v) for k, v in NULL.items()}
    def pvals(labs):
        return {k: ((NULL[k] >= chi2_bloques(Oh, owners, G_of(l))).sum(0) + 1) / (len(NULL[k]) + 1) for k, l in labs.items()}
    P = pvals(obs_labs)
    nsig = sum((P[k] < .05).astype(int) for k in P)
    obs_multi = int((nsig >= 2).sum())
    nulos = []
    for b in range(200):
        Pb = pvals(labs_de(rng.permutation(tipos.values)))
        nulos.append(int((sum((Pb[k] < .05).astype(int) for k in Pb) >= 2).sum()))
    nulos = np.array(nulos)
    print(f"  observado: {obs_multi} ítems con 2+ etiquetas · con el tipo permutado: media {nulos.mean():.1f}, "
          f"p95 {np.percentile(nulos, 95):.0f} · p = {(nulos >= obs_multi).mean():.3f}")
    print("  distribución de cuántas etiquetas toca cada ítem: " +
          " · ".join(f"{k}: {int((nsig == k).sum())}" for k in range(6)))
    pop = np.array([X[q].value_counts(normalize=True).iloc[0] for q in items])
    rho, p = spearmanr(pop, -np.log10(P["tipo"]))
    print(f"  popularidad de la opción más elegida vs. asociación con el tipo: Spearman {rho:+.2f} (p={p:.2f})")
    rho2, p2 = spearmanr(pop, nsig)
    print(f"  popularidad vs. cantidad de etiquetas asociadas: Spearman {rho2:+.2f} (p={p2:.2f})")
    multi = [q for q, k in zip(items, nsig) if k >= 2]
    popul = [q for q, s in zip(items, pop) if s >= .60]
    print(f"  multi-etiqueta ∩ opción popular (≥60%): {sorted(set(multi) & set(popul))} "
          f"({len(set(multi) & set(popul))} de {len(multi)} multi; {len(popul)} populares de {len(items)} ítems)")

    # H2
    per = pd.read_csv(os.path.join(AOUT, "P_por_persona.csv"))
    print("\n== H2 · Acierto de cada clasificador de conjunto según el tipo real (fuera del fold, 20 rep)")
    tab = per.groupby("tipo")[[f"ok_{C.CORTO[c]}" for c in CONJ]].mean()
    tab.columns = [c[3:] for c in tab.columns]
    tab["n"] = per.groupby("tipo").codigo.nunique()
    grupos = pd.DataFrame({C.CORTO[c]: [C.grupo_de(t, c) for t in tab.index] for c in CONJ}, index=tab.index)
    out = tab.copy()
    for c in grupos.columns:
        out[c] = [f"{v:.0%} ({g})" for v, g in zip(tab[c], grupos[c])]
    print(out.to_string())

    # H3
    print("\n== H3 · F1 por tipo (intersección, P_por_persona), con y sin excluidos.txt")
    def f1tab(d):
        rows = []
        for t in sorted(d.tipo.unique()):
            tp = ((d.tipo == t) & (d.pred_inter == t)).sum()
            real = (d.tipo == t).sum(); pred = (d.pred_inter == t).sum()
            pr = tp / pred if pred else 0; rc = tp / real
            rows.append((t, pred / real, pr, rc, 2 * pr * rc / (pr + rc) if pr + rc else 0))
        return pd.DataFrame(rows, columns=["tipo", "pred/real", "precision", "recall", "F1"]).set_index("tipo")
    a, b = f1tab(per), f1tab(per[~per.codigo.isin(list(C.EXCLUIDOS))])
    print(pd.concat({"todos": a, "sin excluidos": b}, axis=1).round(2).to_string())
    print(f"  accuracy {(per.pred_inter == per.tipo).mean():.3f} · F1 macro {a.F1.mean():.3f} · "
          f"acierto balanceado {a.recall.mean():.3f}")

    # H4
    print("\n== H4 · Sensibilidad de «predicho / real» por tipo (bootstrap de personas, 2000)")
    cods = per.codigo.unique()
    bypers = {c: per[per.codigo == c] for c in cods}
    res = collections.defaultdict(list)
    for _ in range(2000):
        d = pd.concat([bypers[c] for c in rng.choice(cods, len(cods))])
        for t in sorted(per.tipo.unique()):
            real = (d.tipo == t).sum()
            if real:
                res[t].append((d.pred_inter == t).sum() / real)
    for t, v in res.items():
        v = np.array(v); nt = per[per.tipo == t].codigo.nunique()
        obs = (per.pred_inter == t).sum() / (per.tipo == t).sum()
        print(f"  tipo {t} (n={nt}): observado {obs:.2f} · IC95 [{np.percentile(v, 2.5):.2f} – {np.percentile(v, 97.5):.2f}]")


if __name__ == "__main__":
    main()
