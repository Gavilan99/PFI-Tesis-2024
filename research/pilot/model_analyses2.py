# -*- coding: utf-8 -*-
"""Análisis del modelo, segunda tanda — sin usar `group_label` en ningún cálculo.

    python model_analyses2.py responses_wide.csv

Todo lo que acá se llama «discriminación» o «asociación» sale SÓLO de las respuestas y de la
etiqueta de cada persona (su tipo, o su grupo en un conjunto, derivado del tipo por la tabla
canónica). Para qué grupo se escribió cada opción no interviene.

  P  predicciones por persona fuera del fold (20 repeticiones): para cada persona, cuántas veces
     se acierta cada conjunto, qué tipos se le predicen y con qué probabilidad — intersección de los
     4 RF y quinto clasificador (tipo directo)
  R2 quitar los ítems menos asociados con la etiqueta, ranking calculado adentro de cada fold con
     χ² ítem × etiqueta — para los 4 clasificadores (cada uno con su etiqueta) y para el quinto
  W  peso igual por tipo: cada persona pesa 1/(personas de su tipo), para medir cuánto influye la
     composición desbalanceada de la muestra

Salidas en analisis_out/. 300 árboles. P y W: 20 repeticiones; R2: 10 (declarado).
"""
import os, sys, collections, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold

import contrast as C
from model_analyses import cargar, scores_tipo, OUT

warnings.filterwarnings("ignore")
CONJ = list(C.GRUPOS)
CORTO = [C.CORTO[c] for c in CONJ]
NT = 300


def rf(seed, cw="balanced"):
    return RandomForestClassifier(NT, class_weight=cw, random_state=seed, n_jobs=-1)


def ajustar(Xtr, ytr, Xte, seed, w=None, cw="balanced", clases=None):
    m = rf(seed, cw).fit(Xtr, ytr, sample_weight=w)
    p = pd.DataFrame(m.predict_proba(Xte), index=Xte.index, columns=m.classes_)
    if clases is not None:
        p = p.reindex(columns=clases, fill_value=0.0)
    return p


def chi2_items(dfi, y):
    """Asociación de cada ítem (todas sus opciones) con la etiqueta y, sin group_label. Devuelve
    −log10(p) del χ² con sus grados de libertad: el χ² crudo crece con el número de celdas y
    favorecería a los Likert (5 opciones) sobre los escenarios (3)."""
    from scipy.stats import chi2 as CHI
    out = {}
    clases = sorted(set(y))
    for q in dfi.columns:
        t = pd.crosstab(dfi[q], y).reindex(columns=clases, fill_value=0).values
        e = t.sum(1, keepdims=True) * t.sum(0, keepdims=True) / t.sum()
        t2 = t[t.sum(1) > 0]
        df_ = (t2.shape[0] - 1) * (t2.shape[1] - 1)
        x = ((t - e) ** 2 / np.where(e == 0, 1, e)).sum()
        out[q] = -np.log10(max(CHI.sf(x, df_), 1e-300)) if df_ > 0 else 0.0
    return pd.Series(out)


def med(s):
    return f"{np.median(s):.0%} [{np.percentile(s, 5):.0%}–{np.percentile(s, 95):.0%}]"


def corrida(X, Y, tipos, reps, cols_por_fold=None, pesos=None, cw="balanced", guardar_personas=False):
    filas, personas = [], []
    for rep in range(reps):
        P = {c: [] for c in CONJ}; D = []
        for f, (tr, te) in enumerate(KFold(5, shuffle=True, random_state=rep).split(X)):
            seed = rep * 100 + f
            w = None if pesos is None else pesos.iloc[tr].values
            for c in CONJ:
                cols = X.columns if cols_por_fold is None else cols_por_fold(tr, c)
                P[c].append(ajustar(X.iloc[tr][cols], Y.iloc[tr][c], X.iloc[te][cols], seed, w, cw,
                                    list(C.GRUPOS[c])))
            cols = X.columns if cols_por_fold is None else cols_por_fold(tr, "tipo")
            D.append(ajustar(X.iloc[tr][cols], tipos.iloc[tr], X.iloc[te][cols], seed, w, cw, list(range(1, 10))))
        pr = {c: pd.concat(v).reindex(X.index) for c, v in P.items()}
        s = scores_tipo(pr); d = pd.concat(D).reindex(X.index)
        fila = {"rep": rep, "M2_interseccion": (s.idxmax(axis=1) == tipos).mean(),
                "M2_directo": (d.idxmax(axis=1) == tipos).mean()}
        for c in CONJ:
            fila[f"M1_{C.CORTO[c]}"] = (pr[c].idxmax(axis=1) == Y[c]).mean()
        filas.append(fila)
        if guardar_personas:
            for p in X.index:
                rk = s.loc[p].sort_values(ascending=False)
                personas.append({"codigo": p, "rep": rep, "tipo": tipos[p],
                                 **{f"ok_{C.CORTO[c]}": int(pr[c].loc[p].idxmax() == Y.at[p, c]) for c in CONJ},
                                 **{f"p_{C.CORTO[c]}": pr[c].at[p, Y.at[p, c]] for c in CONJ},
                                 "pred_inter": int(rk.index[0]), "top3_inter": ",".join(map(str, rk.index[:3])),
                                 "pred_directo": int(d.loc[p].idxmax()), "p_tipo_directo": d.at[p, tipos[p]]})
    return pd.DataFrame(filas), pd.DataFrame(personas)


def main():
    bank, dfi, X, owner, Y, tipos, conf = cargar(sys.argv[1] if len(sys.argv) > 1 else "responses_wide.csv")
    os.makedirs(OUT, exist_ok=True)

    print("== P · Predicciones por persona (20 repeticiones, 300 árboles)", flush=True)
    base, per = corrida(X, Y, tipos, 20, guardar_personas=True)
    per.to_csv(os.path.join(OUT, "P_por_persona.csv"), index=False)
    base.to_csv(os.path.join(OUT, "P_metricas.csv"), index=False)
    print(f"  intersección {med(base.M2_interseccion)} · directo {med(base.M2_directo)} · M1 " +
          " ".join(f"{c} {np.median(base[f'M1_{c}']):.0%}" for c in CORTO), flush=True)

    print("\n== W · Peso igual por tipo (sin class_weight; cada persona pesa 1/n de su tipo)", flush=True)
    cnt = tipos.value_counts()
    w = tipos.map(lambda t: 1 / cnt[t]); w = w / w.mean()
    wb, _ = corrida(X, Y, tipos, 20, pesos=w, cw=None)
    wb.to_csv(os.path.join(OUT, "W_peso_por_tipo.csv"), index=False)
    print(f"  intersección {med(wb.M2_interseccion)} · directo {med(wb.M2_directo)} · M1 " +
          " ".join(f"{c} {np.median(wb[f'M1_{c}']):.0%}" for c in CORTO))
    d = wb.M2_interseccion.values - base.M2_interseccion.values
    print(f"  pareado contra P (mismos folds): intersección Δ mediana {np.median(d):+.1%}, mejora en {(d > 0).sum()}/20", flush=True)

    print("\n== R2 · Quitar ítems menos asociados con la etiqueta (χ² en el fold de entrenamiento; 10 repeticiones)", flush=True)
    filas = []
    for frac in (0.0, 0.25, 0.50):
        def cols_por_fold(tr, objetivo, frac=frac):
            y = tipos.iloc[tr] if objetivo == "tipo" else Y.iloc[tr][objetivo]
            ch = chi2_items(dfi.iloc[tr], y.values).sort_values()
            keep = set(ch.index[int(len(ch) * frac):])
            return [c for c in X.columns if owner[c] in keep]
        r, _ = corrida(X, Y, tipos, 10, cols_por_fold=cols_por_fold)
        r["quitado"] = frac; filas.append(r)
        print(f"  quitando {frac:.0%}: intersección {med(r.M2_interseccion)} · directo {med(r.M2_directo)} · M1 " +
              " ".join(f"{c} {np.median(r[f'M1_{c}']):.0%}" for c in CORTO), flush=True)
    pd.concat(filas).to_csv(os.path.join(OUT, "R2_quitar_items_sin_group_label.csv"), index=False)


if __name__ == "__main__":
    main()
