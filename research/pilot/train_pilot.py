# -*- coding: utf-8 -*-
"""Entrenamiento del piloto: 4 Random Forest + intersección, con selección de features adentro del fold.

    python train_pilot.py responses_wide.csv            # §6 ter, la corrida registrada
    python train_pilot.py responses_wide.csv --estilo   # §6 quater, Enmienda 1

Implementa el protocolo registrado en «NureonAI · Plan de análisis del piloto» §6 ter (2026-10-04).
Con `--estilo` agrega las cuatro columnas de estilo del §6 quater, escribe en `train_out_estilo/`
y, si existe la corrida registrada, imprime la comparación pareada con su regla de decisión.
**No se cambia nada de acá sin enmienda fechada en ese §.** En particular:

· los cuatro tamaños de k se reportan siempre — no se elige el mejor;
· la selección (`SelectKBest` con información mutua) es el primer paso del `Pipeline`, así que se
  ajusta sólo con el fold de entrenamiento de cada clasificador;
· el mismo corte de folds se usa para los cuatro clasificadores, para poder intersectar sobre cada
  persona de test;
· M7 repite todo sin los respondentes de `excluidos.txt` (fuera del entrenamiento y del test);
· desde la Enmienda 2 (plan §6 quinquies) se reporta además un quinto clasificador: un RF que
  predice el tipo directo, con la misma selección y los mismos folds, como comparación fija.
· desde el 2026-10-13 (PDR de la reescritura, «Reporting») se repite además todo SIN los ítems
  reescritos a mitad de recolección (`bank_aliases.json`), con la comparación pareada al final.
  Es una sensibilidad: la corrida registrada sigue siendo TODOS.

Salidas, además de la pantalla:
  train_out/salida.txt                    copia de la pantalla
  train_out/metricas_por_repeticion.csv   una fila por (corrida, k, modelo, repetición)
  train_out/estabilidad.csv               ítem × clasificador × k → veces seleccionado (de 100)
  train_out/recall_por_tipo.csv           tipo × corrida × k → aciertos medios por repetición
"""
import os, sys, collections
import numpy as np, pandas as pd
from scipy.stats import beta
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.dummy import DummyClassifier
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from functools import partial

import contrast as C
from pilot_metrics import con_copias

HERE = C.DATA   # datos y salidas, fuera del repositorio (ver README)
OUT = os.path.join(HERE, "train_out")
N_FOLDS, N_TREES = 5, 500
# 20 es el protocolo. NUREON_REPS sólo existe para probar el cableado rápido; una corrida con
# otro valor no es reportable.
N_REPS = int(os.environ.get("NUREON_REPS", 20))
KS = ["todas", 60, 30, 15]
CONJ = list(C.GRUPOS)


SIN_REESCRITOS = "SIN REESCRITOS"
ESTILO = ["aquiescencia", "punto_medio", "extremos", "concentracion"]
DISCRETAS = None   # máscara de columnas discretas; se fija en main() según la codificación


def codificar(df, bank, estilo=False):
    """Escenarios en one-hot (3 columnas por ítem); Likert como entero 1–5 crudo.
    Con `estilo`, las cuatro columnas del §6 quater: funciones fijas de la fila, sin etiquetas."""
    cols, owner = {}, {}
    lik = []
    for q in [c for c in df.columns if c.startswith("Q")]:
        opts = bank[q]
        v = df[q].astype(int)
        if opts[0]["format"] == "scenario":
            for k in range(1, len(opts) + 1):
                cols[f"{q}_o{k}"] = (v == k).astype(int); owner[f"{q}_o{k}"] = q
        else:
            cols[q] = v; owner[q] = q; lik.append(q)
    X = pd.DataFrame(cols, index=df.index)
    if estilo:
        L = X[lik]
        X["aquiescencia"] = L.mean(axis=1)
        X["punto_medio"] = (L == 3).mean(axis=1)
        X["extremos"] = L.isin([1, 5]).mean(axis=1)
        X["concentracion"] = L.apply(lambda r: r.value_counts().iloc[0] / len(r), axis=1)
        owner.update({c: c for c in ESTILO})
    return X, owner


def selector(k, seed):
    """Información mutua con cada columna tratada según lo que es: los ítems son discretos; las
    columnas de estilo (§6 quater), continuas. Corrección 2026-10-05: tratarlas como discretas hacía
    que cada valor único fuera una categoría y las columnas de estilo salieran elegidas siempre."""
    mi = partial(mutual_info_classif, discrete_features=DISCRETAS if DISCRETAS is not None else True,
                 random_state=seed)
    return SelectKBest(mi, k="all" if k == "todas" else k)


def intersectar(probas):
    """probas: {conj: DataFrame (personas × grupos)} → tipo por argmax de la suma (PDR)."""
    idx = next(iter(probas.values())).index
    score = pd.DataFrame(0.0, index=idx, columns=range(1, 10))
    for conj, p in probas.items():
        for t in range(1, 10):
            score[t] += p[C.grupo_de(t, conj)]
    return score.idxmax(axis=1)


def correr(X, owner, Y, tipos, etiqueta):
    filas, recall, estab = [], collections.defaultdict(list), collections.Counter()
    for rep in range(N_REPS):
        kf = KFold(N_FOLDS, shuffle=True, random_state=rep)
        pred = {(k, m): {c: [] for c in CONJ} for k in KS for m in ("RF", "DT")}
        dummy = {c: [] for c in CONJ}
        directo = {k: [] for k in KS}   # quinto clasificador: tipo directo (Enmienda 2, plan §6 quinquies)
        for f, (tr, te) in enumerate(kf.split(X)):
            seed = rep * 100 + f
            for k in KS:
                pipe = Pipeline([("sel", selector(k, seed)),
                                 ("clf", RandomForestClassifier(N_TREES, class_weight="balanced",
                                                                random_state=seed, n_jobs=-1))]).fit(X.iloc[tr], tipos.iloc[tr])
                directo[k].append(pd.Series(pipe.predict(X.iloc[te]), index=X.index[te]))
            for conj in CONJ:
                ytr = Y[conj].iloc[tr]
                d = DummyClassifier(strategy="most_frequent").fit(X.iloc[tr], ytr)
                dummy[conj].append(pd.Series(d.predict(X.iloc[te]), index=X.index[te]))
                for k in KS:
                    for m, est in (("RF", RandomForestClassifier(N_TREES, class_weight="balanced",
                                                                 random_state=seed, n_jobs=-1)),
                                   ("DT", DecisionTreeClassifier(class_weight="balanced", random_state=seed))):
                        pipe = Pipeline([("sel", selector(k, seed)), ("clf", est)]).fit(X.iloc[tr], ytr)
                        p = pd.DataFrame(pipe.predict_proba(X.iloc[te]), index=X.index[te],
                                         columns=pipe.classes_)
                        for g in C.GRUPOS[conj]:
                            if g not in p:
                                p[g] = 0.0
                        pred[(k, m)][conj].append(p)
                        if m == "RF":
                            sel = X.columns[pipe.named_steps["sel"].get_support()]
                            for q in {owner[c] for c in sel}:
                                estab[(q, C.CORTO[conj], k)] += 1
        # métricas de la repetición
        base = {c: (pd.concat(dummy[c]).reindex(X.index) == Y[c]).mean() for c in CONJ}
        for (k, m), por_conj in pred.items():
            probas = {c: pd.concat(v).reindex(X.index) for c, v in por_conj.items()}
            aciertos = {c: (probas[c].idxmax(axis=1) == Y[c]) for c in CONJ}
            t_pred = intersectar(probas)
            ok_tipo = t_pred == tipos
            n_ok = sum(aciertos[c].astype(int) for c in CONJ)
            fila = {"corrida": etiqueta, "k": k, "modelo": m, "rep": rep,
                    "M2_tipo": ok_tipo.mean(), "M3_3de4": (n_ok >= 3).mean(),
                    "M2_directo": (pd.concat(directo[k]).reindex(X.index) == tipos).mean() if m == "RF" else np.nan}
            for c in CONJ:
                fila[f"M1_{C.CORTO[c]}"] = aciertos[c].mean()
                fila[f"base_{C.CORTO[c]}"] = base[c]
            filas.append(fila)
            if m == "RF":
                for t in range(1, 10):
                    sel = tipos == t
                    if sel.any():
                        recall[(t, k)].append(int(ok_tipo[sel].sum()))
    return pd.DataFrame(filas), recall, estab


def rango(s):
    return f"{s.median():.0%} [{s.quantile(.05):.0%}–{s.quantile(.95):.0%}]"


def cp(x, n):
    lo = beta.ppf(.025, x, n - x + 1) if x > 0 else 0.0
    hi = beta.ppf(.975, x + 1, n - x) if x < n else 1.0
    return lo, hi


def reportar(df, recall, tipos, etiqueta):
    print(f"\n{'=' * 72}\n{etiqueta} — n={len(tipos)} · {N_FOLDS} folds × {N_REPS} repeticiones\n"
          f"mediana [p5–p95] entre repeticiones")
    base = df[(df.k == "todas") & (df.modelo == "RF")]
    print("\nM1 · por conjunto")
    print(f"  {'':16}" + "".join(f"{C.CORTO[c]:>22}" for c in CONJ))
    print(f"  {'base mayoritaria':16}" + "".join(f"{rango(base[f'base_{C.CORTO[c]}']):>22}" for c in CONJ))
    for m in ("RF", "DT"):
        for k in KS:
            d = df[(df.k == k) & (df.modelo == m)]
            print(f"  {m + ' k=' + str(k):16}" + "".join(f"{rango(d[f'M1_{C.CORTO[c]}']):>22}" for c in CONJ))
    mayor = tipos.value_counts().iloc[0] / len(tipos)
    print(f"\nM2 · tipo exacto (base «tipo más común» {mayor:.0%}, azar 11%) · M3 · ≥3 de 4")
    for m in ("RF", "DT"):
        for k in KS:
            d = df[(df.k == k) & (df.modelo == m)]
            extra = f"   quinto (tipo directo) {rango(d.M2_directo):>18}" if m == "RF" and "M2_directo" in d else ""
            print(f"  {m + ' k=' + str(k):16} M2 {rango(d.M2_tipo):>18}   M3 {rango(d.M3_3de4):>18}" + extra)
    print("\nM10 · recall por tipo (RF), aciertos medios por repetición")
    cnt = tipos.value_counts()
    for t in range(1, 10):
        n = int(cnt.get(t, 0))
        if not n:
            print(f"  tipo {t}: ausente"); continue
        celdas = []
        for k in KS:
            x = np.mean(recall[(t, k)])
            if n >= 4:
                lo, hi = cp(round(x), n)
                celdas.append(f"k={k}: {x:.1f}/{n} [{lo:.0%}–{hi:.0%}]")
            else:
                celdas.append(f"k={k}: {x:.1f}/{n}")
        print(f"  tipo {t}: " + " · ".join(celdas))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); return 2
    global OUT
    estilo = "--estilo" in sys.argv
    if estilo:
        OUT = os.path.join(HERE, "train_out_estilo")
    bank, B, _ = con_copias()
    df = pd.read_csv(args[0], dtype=str).set_index("respondent_id")
    df = df[[c for c in df.columns if c.startswith("Q")]]
    df = df[[bool(B.get(c) and B[c].get("tipo_asignado")) for c in df.index]]
    tipos = pd.Series({c: int(B[c]["tipo_asignado"]) for c in df.index})
    X, owner = codificar(df, bank, estilo)
    global DISCRETAS
    DISCRETAS = np.array([c not in ESTILO for c in X.columns])
    Y = pd.DataFrame({c: [C.grupo_de(t, c) for t in tipos] for c in CONJ}, index=X.index)
    os.makedirs(OUT, exist_ok=True)
    sys.stdout = Tee(os.path.join(OUT, "salida.txt"))
    print(f"{len(X)} respondentes · {X.shape[1]} columnas ({len(set(owner.values()))} ítems)")

    reescritos = items_reescritos()
    cols_sin = [c for c in X.columns if owner[c] not in reescritos]
    print(f"ítems reescritos a mitad de recolección (PDR): {len(reescritos)} · sin ellos quedan "
          f"{len(cols_sin)} columnas ({len({owner[c] for c in cols_sin})} ítems)")

    todas, recs = [], {}
    estab_total = None
    for etiqueta, mask, cols in (("TODOS", X.index == X.index, list(X.columns)),
                                 ("M7 · SIN EXCLUIDOS", ~X.index.isin(list(C.EXCLUIDOS)), list(X.columns)),
                                 (SIN_REESCRITOS, X.index == X.index, cols_sin)):
        if etiqueta == SIN_REESCRITOS:
            DISCRETAS = np.array([c not in ESTILO for c in cols])
        d, rec, est = correr(X.loc[mask, cols], owner, Y[mask], tipos[mask], etiqueta)
        todas.append(d); recs[etiqueta] = rec
        reportar(d, rec, tipos[mask], etiqueta)
        if etiqueta == "TODOS":
            estab_total = est
    DISCRETAS = np.array([c not in ESTILO for c in X.columns])
    comparar_reescritos(pd.concat(todas))

    pd.concat(todas).to_csv(os.path.join(OUT, "metricas_por_repeticion.csv"), index=False)
    pd.DataFrame([{"tipo": t, "k": k, "corrida": e, "aciertos_medios": np.mean(v)}
                  for e, r in recs.items() for (t, k), v in r.items()]
                 ).to_csv(os.path.join(OUT, "recall_por_tipo.csv"), index=False)
    total = N_FOLDS * N_REPS
    est = pd.DataFrame([{"item": q, "clasificador": c, "k": k, "veces": v}
                        for (q, c, k), v in estab_total.items()])
    est.to_csv(os.path.join(OUT, "estabilidad.csv"), index=False)

    print(f"\n{'=' * 72}\nESTABILIDAD (corrida TODOS) — veces seleccionado de {total}")
    items = sorted(set(owner.values()))
    for k in KS[1:]:
        e = est[est.k == k]
        piv = e.pivot_table(index="item", columns="clasificador", values="veces",
                            fill_value=0).reindex(items, fill_value=0)
        nunca = [q for q in items if piv.loc[q].max() == 0]
        top = piv.max(axis=1).sort_values(ascending=False)
        print(f"\n  k={k}: ítems con ≥80/{total} en algún clasificador: {int((top >= 80).sum())} · "
              f"nunca en ninguno: {len(nunca)}")
        for c in piv.columns:
            s = piv[c].sort_values(ascending=False)
            print(f"    {c:11} top: " + ", ".join(f"{q} {int(v)}" for q, v in s.head(6).items()))
        if estilo:
            print("    columnas de estilo: " + " · ".join(
                f"{e} " + "/".join(str(int(piv.loc[e, c])) if e in piv.index else "0" for c in piv.columns)
                for e in ESTILO) + f"  (de {total}, por {'/'.join(piv.columns)})")
    if estilo:
        comparar_enmienda()
    return 0


def items_reescritos():
    """Ítems con algún cambio de redacción a mitad de recolección (PDR, `bank_aliases.json`)."""
    import json
    al = json.load(open(os.path.join(C.BANK_DIR, "bank_aliases.json"), encoding="utf-8"))
    return {c["question_id"] for c in al["cambios"]}


def comparar_reescritos(df):
    """PDR · Reporting: la corrida con y sin los ítems reescritos, pareada por repetición (mismos folds)."""
    key = ["k", "modelo", "rep"]
    a = df[df.corrida == "TODOS"].set_index(key); b = df[df.corrida == SIN_REESCRITOS].set_index(key)
    print(f"\n{'=' * 72}\nREESCRITOS · comparación pareada (sin los ítems reescritos − con todos), RF")
    for k in KS:
        x, y = a.xs((k, "RF"), level=("k", "modelo")), b.xs((k, "RF"), level=("k", "modelo"))
        dm = y.M2_tipo - x.M2_tipo
        print(f"  k={str(k):6} M2: mediana Δ {dm.median():+.1%} · sin reescritos mejor en {int((dm > 0).sum())}/{len(dm)}"
              " · M1 Δ " + " ".join(f"{C.CORTO[c]} {(y[f'M1_{C.CORTO[c]}'] - x[f'M1_{C.CORTO[c]}']).median():+.1%}"
                                    for c in CONJ))


class Tee:
    """Copia la salida de pantalla a `salida.txt` de la carpeta de salida (antes era una copia a mano
    que podía quedar vieja)."""
    def __init__(self, path):
        self.f, self.o = open(path, "w", encoding="utf-8"), sys.stdout

    def write(self, s):
        self.o.write(s); self.f.write(s)

    def flush(self):
        self.o.flush(); self.f.flush()


def comparar_enmienda():
    """§6 quater: comparación pareada por repetición contra la corrida registrada."""
    base_p = os.path.join(HERE, "train_out", "metricas_por_repeticion.csv")
    if not os.path.exists(base_p):
        print("\n(no hay corrida registrada en train_out/ — sin comparación)"); return
    a = pd.read_csv(base_p, dtype={"k": str}); b = pd.read_csv(os.path.join(OUT, "metricas_por_repeticion.csv"), dtype={"k": str})
    key = ["corrida", "k", "modelo", "rep"]
    m = a.merge(b, on=key, suffixes=("_base", "_estilo"))
    print(f"\n{'=' * 72}\nENMIENDA 1 · comparación pareada (con estilo − sin estilo), RF")
    for k in [str(x) for x in KS]:
        d = m[(m.k == k) & (m.modelo == "RF") & (m.corrida == "TODOS")]
        dm = d.M2_tipo_estilo - d.M2_tipo_base
        mejoras = int((dm > 0).sum())
        linea = f"  k={k:6} M2: mediana Δ {dm.median():+.1%} · mejora en {mejoras}/{len(d)}"
        linea += " · M1 Δ " + " ".join(f"{C.CORTO[c]} {(d[f'M1_{C.CORTO[c]}_estilo'] - d[f'M1_{C.CORTO[c]}_base']).median():+.1%}" for c in CONJ)
        print(linea)
        if k == "todas":
            adopta = dm.median() > 0 and mejoras >= 15
            print(f"  REGLA (k=todas): mediana > 0 y ≥15/20 → {'SE ADOPTA' if adopta else 'NO se adopta'}")


if __name__ == "__main__":
    sys.exit(main())
