# -*- coding: utf-8 -*-
"""Análisis del modelo, tercera tanda.

    python model_analyses3.py responses_wide.csv

  G   grupo predicho por persona y conjunto (20 repeticiones, fuera del fold): matrices de confusión
      por conjunto (grupo real × grupo predicho) y acierto de cada conjunto según el tipo real
  S8  ¿qué cambia sin los ítems que el selector nunca eligió con 30 columnas (leídos de la última corrida)?

300 árboles, class_weight balanceado, todas las columnas — igual que P en model_analyses2.
Salidas en analisis_out/.
"""
import os, sys, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold

import contrast as C
from model_analyses import cargar, scores_tipo, OUT

warnings.filterwarnings("ignore")
CONJ = list(C.GRUPOS)
NT, REPS = 300, 20
# Los ítems que el selector nunca eligió con 30 columnas, leídos de la última corrida registrada
# (train_pilot.py → train_out/estabilidad.csv). Antes era una lista fija de la corrida de n=44.
def nunca_30():
    here = os.path.dirname(os.path.abspath(__file__))
    for base in (getattr(C, "DATA", None), here, getattr(C, "PROJ", None)):
        p = base and os.path.join(base, "train_out", "estabilidad.csv")
        if p and os.path.exists(p):
            e = pd.read_csv(p, dtype={"k": str}); s = e[e.k == "30"].groupby("item").veces.max()
            out = sorted(i for i in set(e.item) if s.get(i, 0) == 0)
            print(f"  (ítems nunca elegidos con k=30, desde {p}: {len(out)})")
            return out
    raise SystemExit("falta train_out/estabilidad.csv: correr antes train_pilot.py")


def corrida(X, tipos, guardar=False):
    Y = pd.DataFrame({c: [C.grupo_de(t, c) for t in tipos] for c in CONJ}, index=X.index)
    filas, per = [], []
    for rep in range(REPS):
        P = {c: [] for c in CONJ}
        for f, (tr, te) in enumerate(KFold(5, shuffle=True, random_state=rep).split(X)):
            for c in CONJ:
                m = RandomForestClassifier(NT, class_weight="balanced", random_state=rep * 100 + f,
                                           n_jobs=-1).fit(X.iloc[tr], Y.iloc[tr][c])
                P[c].append(pd.DataFrame(m.predict_proba(X.iloc[te]), index=X.index[te],
                                         columns=m.classes_).reindex(columns=list(C.GRUPOS[c]), fill_value=0))
        pr = {c: pd.concat(v).reindex(X.index) for c, v in P.items()}
        s = scores_tipo(pr); tp = s.idxmax(axis=1)
        filas.append({"rep": rep, "M2": (tp == tipos).mean(),
                      **{f"M1_{C.CORTO[c]}": (pr[c].idxmax(axis=1) == Y[c]).mean() for c in CONJ}})
        if guardar:
            for p in X.index:
                per.append({"codigo": p, "rep": rep, "tipo": tipos[p], "pred_tipo": int(tp[p]),
                            **{f"real_{C.CORTO[c]}": Y.at[p, c] for c in CONJ},
                            **{f"pred_{C.CORTO[c]}": pr[c].loc[p].idxmax() for c in CONJ}})
    return pd.DataFrame(filas), pd.DataFrame(per)


def med(s):
    return f"{np.median(s):.0%} [{np.percentile(s, 5):.0%}–{np.percentile(s, 95):.0%}]"


def resumen(nom, d, base=None):
    txt = f"  {nom:22} M2 {med(d.M2)} · M1 " + " ".join(f"{C.CORTO[c]} {np.median(d[f'M1_{C.CORTO[c]}']):.0%}" for c in CONJ)
    if base is not None:
        dd = d.M2.values - base.M2.values
        txt += f"  · Δ M2 pareado {np.median(dd):+.1%} (mejora en {(dd > 0).sum()}/{REPS}, empeora en {(dd < 0).sum()})"
    print(txt, flush=True)


def main():
    bank, dfi, X, owner, Y, tipos, conf = cargar(sys.argv[1] if len(sys.argv) > 1 else "responses_wide.csv")
    print("== G · base, guardando el grupo predicho por persona", flush=True)
    base, per = corrida(X, tipos, guardar=True)
    per.to_csv(os.path.join(OUT, "G_grupo_predicho_por_persona.csv"), index=False)
    resumen("base", base)


    NUNCA_30 = nunca_30()
    print(f"\n== S8 · sin los {len(NUNCA_30)} ítems nunca seleccionados (k=30)", flush=True)
    cols = [c for c in X.columns if owner[c] not in NUNCA_30]
    d8, _ = corrida(X[cols], tipos)
    resumen(f"sin {len(NUNCA_30)} ítems ({len(cols)} col.)", d8, base)
    pd.concat([base.assign(escenario="base"), d8.assign(escenario="sin 8")]
              ).to_csv(os.path.join(OUT, "escenarios_sin8.csv"), index=False)


if __name__ == "__main__":
    main()
