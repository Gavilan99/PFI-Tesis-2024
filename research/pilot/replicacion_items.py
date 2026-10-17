# -*- coding: utf-8 -*-
"""Replicación de la asociación ítem × etiqueta (2026-10-14).

    python replicacion_items.py

Toma los ítems con p<.05 por etiqueta en el EDA de n=44 (eda_out_n44/G1_item_x_etiqueta.csv) y los
prueba SÓLO en las personas que respondieron después (las que no están en analisis_out_n44). Control:
los ítems no señalados, en las mismas personas. χ² por permutación (2000; 1000 en el control).
Datos: responses_wide_n70_analisis.csv (copia fija del corte n=70).
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
import contrast as C
from eda_pilot import cargar
from eda_extra2 import v_cramer
from scipy.stats import spearmanr
bank, X, tipos, Y, fmt = cargar("responses_wide_n70_analisis.csv")
old = set(pd.read_csv("analisis_out_n44/P_resumen_por_persona.csv").codigo)
new = [c for c in X.index if c not in old]
print("personas n=44:", len(old & set(X.index)), "· nuevas:", len(new))
g1 = pd.read_csv("eda_out_n44/G1_item_x_etiqueta.csv")
labs = {**{C.CORTO[c]: Y[C.CORTO[c]] for c in C.GRUPOS}, "tipo": tipos}
rng = np.random.default_rng(0)
def oh(v):
    u, i = np.unique(v, return_inverse=True); return np.eye(len(u))[i]
def chis(R, G):  # R n×a, G B×n×b
    t = np.einsum("na,Bnb->Bab", R, G); e = t.sum(2, keepdims=True) * t.sum(1, keepdims=True) / len(R)
    return ((t - e) ** 2 / np.where(e == 0, 1, e)).sum((1, 2))
def test(q, lab, idx, B=2000):
    R = oh(X.loc[idx, q].values); g = lab.loc[idx].values; Gm = oh(g)
    x0 = chis(R, Gm[None])[0]
    perm = np.array([rng.permutation(len(g)) for _ in range(B)])
    null = chis(R, Gm[perm])
    return ((null >= x0).sum() + 1) / (B + 1), v_cramer(x0, len(R), R.shape[1], Gm.shape[1])
for obj in labs:
    sub = g1[g1.objetivo == obj]
    flag = sub[sub.p < .05].item.tolist()
    res = [test(q, labs[obj], new) for q in flag]
    hits = sum(p < .05 for p, _ in res)
    # control: ítems NO señalados en n=44
    ctrl = sub[sub.p >= .05].item.values
    rc = [test(q, labs[obj], new, 1000)[0] for q in ctrl]
    print(f"{obj:11} señalados en n=44: {len(flag):2} · en las nuevas p<.05: {hits}/{len(flag)} ({hits/max(len(flag),1):.0%}) · "
          f"control (no señalados): {sum(p < .05 for p in rc)}/{len(rc)} ({np.mean([p < .05 for p in rc]):.0%}) · " + ", ".join(f"{q} p={p:.2f}" for q, (p, v) in zip(flag, res) if p < .2))
# Q065, Q130, Q028 en las nuevas
for q, obj in (("Q065", "Relaciones"), ("Q130", "Armónico"), ("Q130", "Relaciones"), ("Q028", "Armónico"), ("Q075", "tipo")):
    p, v = test(q, labs[obj], new); print(f"  {q} → {obj}: nuevas p={p:.3f} V={v:.2f}")
