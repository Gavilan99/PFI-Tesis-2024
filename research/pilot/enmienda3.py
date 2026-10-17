# -*- coding: utf-8 -*-
"""Enmienda 3 (plan §6 sexies): selección de columnas por conjunto, con validación prospectiva.

    python enmienda3.py responses_wide.csv --cv            # prueba exploratoria (SESGADA a favor de B)
    python enmienda3.py responses_wide.csv --prospectivo   # la evaluación que decide

Configuraciones:
  A   los 4 clasificadores con todas las columnas            (registrada, §6 ter)
  B   Armónico y Relaciones con 30 columnas; Centros y Horneviano con todas   (enmienda)
  A+E / B+E   lo mismo con las 4 columnas de estilo del §6 quater (exploratorio)

--cv  Validación cruzada 5 × 20 sobre las personas actuales, con los MISMOS folds y semillas que
      `train_pilot.py`, así que A reproduce la corrida registrada. Como B se eligió mirando estos
      datos, esta comparación lo favorece por construcción: se reporta, no decide.
--prospectivo  Entrena con las personas congeladas en `e3_entrenamiento.txt` y evalúa SÓLO a las
      que respondieron después. Promedia las probabilidades de 20 semillas. Aplica la regla de
      decisión registrada. Ésta es la evaluación que vale.

Ambos modos corren con y sin los respondentes de `excluidos.txt` en el entrenamiento.
"""
import os, sys, warnings
import numpy as np, pandas as pd
from functools import partial
from scipy.stats import binomtest
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.model_selection import KFold

import contrast as C
from pilot_metrics import con_copias
from train_pilot import codificar, ESTILO

warnings.filterwarnings("ignore")
HERE = C.DATA   # datos y salidas, fuera del repositorio (ver README)
OUT = os.path.join(HERE, "e3_out")
CONJ = list(C.GRUPOS)
K_B = {"Conjunto Armónico": 30, "Conjunto de Relaciones Objetales": 30}
N_TREES, N_REPS = 500, 20
CONGELADO = os.path.join(HERE, "e3_entrenamiento.txt")


def ajustar(Xtr, ytr, Xte, k, seed):
    """Selección (si k) ajustada sólo con el entrenamiento, después RF. Devuelve probabilidades."""
    cols = list(Xtr.columns)
    if k is not None:
        disc = np.array([c not in ESTILO for c in cols])
        mi = partial(mutual_info_classif, discrete_features=disc, random_state=seed)
        sel = SelectKBest(mi, k=k).fit(Xtr, ytr)
        cols = list(np.array(cols)[sel.get_support()])
    m = RandomForestClassifier(N_TREES, class_weight="balanced", random_state=seed,
                               n_jobs=-1).fit(Xtr[cols], ytr)
    return pd.DataFrame(m.predict_proba(Xte[cols]), index=Xte.index, columns=m.classes_)


def scores(probas):
    idx = next(iter(probas.values())).index
    s = pd.DataFrame(0.0, index=idx, columns=range(1, 10))
    for conj, p in probas.items():
        for t in range(1, 10):
            g = C.grupo_de(t, conj)
            s[t] += p[g] if g in p else 0.0
    return s


def predicciones(Xtr, Ytr, Xte, seeds):
    """Para A y B (y las variantes +E si Xtr trae estilo): probas por conjunto promediadas en seeds."""
    out = {}
    for conj in CONJ:
        for cfg in ("A", "B"):
            k = K_B.get(conj) if cfg == "B" else None
            if cfg == "B" and k is None:
                continue                                    # B = A en Centros y Horneviano
            ps = [ajustar(Xtr, Ytr[conj], Xte, k, s) for s in seeds]
            out[(cfg, conj)] = sum(ps) / len(ps)
    res = {}
    for cfg in ("A", "B"):
        pr = {c: out.get((cfg, c), out[("A", c)]) for c in CONJ}
        res[cfg] = pr
    return res


def evaluar(pr, Y, tipos):
    ok = pd.DataFrame({C.CORTO[c]: pr[c].idxmax(axis=1) == Y.loc[pr[c].index, c] for c in CONJ})
    tipo_ok = scores(pr).idxmax(axis=1) == tipos.loc[ok.index]
    return ok, tipo_ok


def cargar(path):
    """Lee respuestas y archivo B UNA sola vez y devuelve las dos codificaciones (sin y con estilo).
    Leer dos veces durante una corrida larga mezcló muestras distintas el 2026-10-12 (el archivo B y
    responses_wide.csv cambiaron a mitad de la corrida)."""
    bank, B, _ = con_copias()
    df = pd.read_csv(path, dtype=str).set_index("respondent_id")
    df = df[[c for c in df.columns if c.startswith("Q")]]
    df = df[[bool(B.get(c) and B[c].get("tipo_asignado")) for c in df.index]]
    tipos = pd.Series({c: int(B[c]["tipo_asignado"]) for c in df.index})
    X0, _ = codificar(df, bank, False); X1, _ = codificar(df, bank, True)
    Y = pd.DataFrame({c: [C.grupo_de(t, c) for t in tipos] for c in CONJ}, index=X0.index)
    return {False: X0, True: X1}, Y, tipos


def congelados():
    return [l.strip() for l in open(CONGELADO, encoding="utf-8") if l.strip() and not l.startswith("#")]


def modo_cv(path):
    os.makedirs(OUT, exist_ok=True)
    filas = []
    XX, Yall, Tall = cargar(path)
    cong = [c for c in congelados() if c in Yall.index]
    print(f"muestra de la prueba: las {len(cong)} personas congeladas · tipos " +
          " · ".join(f"{t}×{n}" for t, n in sorted(Tall[cong].value_counts().items())), flush=True)
    for estilo in (False, True):
        Xall, Yall_, Tall_ = XX[estilo].loc[cong], Yall.loc[cong], Tall.loc[cong]
        for nom, mask in (("todos", Xall.index == Xall.index), ("sin excluidos", ~Xall.index.isin(list(C.EXCLUIDOS)))):
            X, Y, T = Xall[mask], Yall_[mask], Tall_[mask]
            for rep in range(N_REPS):
                acc = {cfg: {c: [] for c in CONJ} for cfg in ("A", "B")}
                for f, (tr, te) in enumerate(KFold(5, shuffle=True, random_state=rep).split(X)):
                    pr = predicciones(X.iloc[tr], Y.iloc[tr], X.iloc[te], [rep * 100 + f])
                    for cfg in pr:
                        for c in CONJ:
                            acc[cfg][c].append(pr[cfg][c])
                for cfg in ("A", "B"):
                    pr = {c: pd.concat(v).reindex(X.index) for c, v in acc[cfg].items()}
                    ok, tok = evaluar(pr, Y, T)
                    filas.append({"estilo": estilo, "muestra": nom, "config": cfg + ("+E" if estilo else ""),
                                  "rep": rep, "M2": tok.mean(), **{f"M1_{c}": ok[c].mean() for c in ok}})
            print(f"  hecho: estilo={estilo} · {nom}", flush=True)
    d = pd.DataFrame(filas); d.to_csv(os.path.join(OUT, "cv_exploratoria.csv"), index=False)
    md = lambda s: f"{np.median(s):.0%} [{np.percentile(s, 5):.0%}–{np.percentile(s, 95):.0%}]"
    print("\nPRUEBA EXPLORATORIA (validación cruzada 5×20; B se eligió con estos datos: SESGADA a favor de B)")
    for nom in ("todos", "sin excluidos"):
        print(f"\n  {nom}")
        for cfg in ("A", "B", "A+E", "B+E"):
            x = d[(d.muestra == nom) & (d.config == cfg)]
            print(f"    {cfg:4} M2 {md(x.M2):>14} · M1 " +
                  " ".join(f"{c} {np.median(x[f'M1_{c}']):.0%}" for c in [C.CORTO[k] for k in CONJ]))
        base = d[(d.muestra == nom) & (d.config == "A")].set_index("rep")
        for cfg in ("B", "A+E", "B+E"):
            x = d[(d.muestra == nom) & (d.config == cfg)].set_index("rep")
            dm = x.M2 - base.M2
            m1 = x[[c for c in x if c.startswith("M1_")]].mean(axis=1) - base[[c for c in base if c.startswith("M1_")]].mean(axis=1)
            print(f"    {cfg} − A pareado: M2 Δ {np.median(dm):+.1%} (mejora en {(dm > 0).sum()}/20) · "
                  f"M1 medio Δ {np.median(m1):+.1%} (mejora en {(m1 > 0).sum()}/20)")


def modo_prospectivo(path):
    cong_ids = congelados()
    XX, Y, T = cargar(path); X = XX[False]
    nuevos = [c for c in X.index if c not in cong_ids]
    print(f"entrenamiento congelado: {len(cong_ids)} · personas nuevas con tipo: {len(nuevos)} {nuevos}")
    if not nuevos:
        print("Todavía no hay personas nuevas: no hay nada que evaluar."); return 0
    for nom, tr_ids in (("todos", [c for c in cong_ids if c in X.index]),
                        ("sin excluidos", [c for c in cong_ids if c in X.index and c not in C.EXCLUIDOS])):
        pr = predicciones(X.loc[tr_ids], Y.loc[tr_ids], X.loc[nuevos], list(range(20)))
        okA, tA = evaluar(pr["A"], Y, T); okB, tB = evaluar(pr["B"], Y, T)
        a, b = okA.sum(axis=1), okB.sum(axis=1)
        up, dn = int((b > a).sum()), int((b < a).sum())
        p = binomtest(up, up + dn, .5, alternative="greater").pvalue if up + dn else float("nan")
        adopta = len(nuevos) >= 15 and b.sum() > a.sum() and tB.sum() >= tA.sum()
        print(f"\n  {nom} · {len(nuevos)} personas nuevas")
        print(f"    conjuntos acertados: A {int(a.sum())}/{4*len(nuevos)} · B {int(b.sum())}/{4*len(nuevos)}")
        print(f"    tipo acertado:       A {int(tA.sum())}/{len(nuevos)} · B {int(tB.sum())}/{len(nuevos)}")
        print(f"    por persona: B mejor en {up}, peor en {dn}, igual en {len(nuevos) - up - dn} · signos p={p:.3f}")
        print("    REGLA: " + ("SE ADOPTA B" if adopta else
                              "no se adopta" + (" (menos de 15 personas nuevas)" if len(nuevos) < 15 else "")))
    return 0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); return 2
    if "--cv" in sys.argv:
        modo_cv(args[0])
    if "--prospectivo" in sys.argv:
        modo_prospectivo(args[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
