# -*- coding: utf-8 -*-
"""Análisis del modelo sobre la muestra del piloto — los que necesitan entrenar.

    python model_analyses.py responses_wide.csv [--solo C,A,...]

Son exploratorios: NO reemplazan a la corrida registrada (`train_pilot.py`, plan §6 ter), y
ninguno se usa para elegir la configuración que se reporta como resultado del piloto.

  C  top-k y calibración — ¿el tipo real está entre los 2 o 3 más probables? ¿el modelo sabe
     cuándo acierta? (mismos folds y RF que la corrida registrada, k=todas, 500 árboles)
  E  matriz de errores por tipo — a qué tipo va cada uno, y qué conjunto comparten real y
     predicho (por diseño, dos tipos distintos comparten siempre exactamente un grupo)
  T  quinto clasificador — un RF que predice el tipo directo (9 clases), en los mismos folds
  L  calidad de etiquetas — la misma evaluación sólo con confianza alta / sin confianza baja
  R  quitar los ítems que menos discriminan — calculado ADENTRO de cada fold (sin fuga)
  A  curva de aprendizaje — acierto según cuánta gente hay para entrenar
  D  largo del test — acierto según cuántos ítems se responden
  B  techo por simulación — personas sintéticas generadas desde las respuestas reales

Salidas en analisis_out/ (CSV + PNG). Semillas fijas. C, E y T usan 500 árboles, como la corrida
registrada; L, R, A, D y B usan 300 para que el conjunto entre en ~1,5 h (la diferencia entre 300 y
500 árboles es mucho menor que la variación entre repeticiones).
"""
import os, sys, collections, warnings, time
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold

import contrast as C
from pilot_metrics import con_copias
from train_pilot import codificar, intersectar

warnings.filterwarnings("ignore")
HERE = C.DATA   # datos y salidas, fuera del repositorio (ver README)
OUT = os.path.join(HERE, "analisis_out")
CONJ = list(C.GRUPOS)
CORTO = [C.CORTO[c] for c in CONJ]
N_REPS, N_FOLDS = 20, 5


def rf(n, seed):
    return RandomForestClassifier(n, class_weight="balanced", random_state=seed, n_jobs=-1)


def cargar(path):
    bank, B, _ = con_copias()
    df = pd.read_csv(path, dtype=str).set_index("respondent_id")
    df = df[[c for c in df.columns if c.startswith("Q")]]
    df = df[[bool(B.get(c) and B[c].get("tipo_asignado")) for c in df.index]]
    tipos = pd.Series({c: int(B[c]["tipo_asignado"]) for c in df.index})
    conf = pd.Series({c: (B[c].get("confianza") or "").strip() for c in df.index})
    X, owner = codificar(df, bank)
    Y = pd.DataFrame({c: [C.grupo_de(t, c) for t in tipos] for c in CONJ}, index=X.index)
    return bank, df.astype(int), X, owner, Y, tipos, conf


def probas_fold(Xtr, Ytr, Xte, n_trees, seed):
    out = {}
    for conj in CONJ:
        m = rf(n_trees, seed).fit(Xtr, Ytr[conj])
        p = pd.DataFrame(m.predict_proba(Xte), index=Xte.index, columns=m.classes_)
        for g in C.GRUPOS[conj]:
            if g not in p:
                p[g] = 0.0
        out[conj] = p
    return out


def scores_tipo(probas):
    idx = next(iter(probas.values())).index
    s = pd.DataFrame(0.0, index=idx, columns=range(1, 10))
    for conj, p in probas.items():
        for t in range(1, 10):
            s[t] += p[C.grupo_de(t, conj)]
    return s


def metricas(probas, Y, tipos):
    s = scores_tipo(probas)
    m = {f"M1_{C.CORTO[c]}": (probas[c].idxmax(axis=1) == Y.loc[probas[c].index, c]).mean() for c in CONJ}
    m["M2"] = (s.idxmax(axis=1) == tipos.loc[s.index]).mean()
    return m


def cv_basica(X, Y, tipos, n_trees, reps=N_REPS, cols=None, seed0=0):
    """Validación cruzada repetida; devuelve un DataFrame de métricas por repetición."""
    filas = []
    Xc = X if cols is None else X[cols]
    for rep in range(reps):
        allp = {c: [] for c in CONJ}
        for f, (tr, te) in enumerate(KFold(N_FOLDS, shuffle=True, random_state=rep).split(Xc)):
            p = probas_fold(Xc.iloc[tr], Y.iloc[tr], Xc.iloc[te], n_trees, seed0 + rep * 100 + f)
            for c in CONJ:
                allp[c].append(p[c])
        pr = {c: pd.concat(v).reindex(Xc.index) for c, v in allp.items()}
        filas.append({"rep": rep, **metricas(pr, Y, tipos)})
    return pd.DataFrame(filas)


def med(s):
    return f"{np.median(s):.0%} [{np.percentile(s, 5):.0%}–{np.percentile(s, 95):.0%}]"


# ─────────────────────────── C · E · T ───────────────────────────
def analisis_CET(X, Y, tipos):
    print("\n== C · E · T — mismos folds y RF que la corrida registrada (k=todas, 500 árboles)")
    topk = collections.defaultdict(list); topk_T = collections.defaultdict(list)
    marg, conf_mat = [], np.zeros((10, 10), int)
    filasT = []
    for rep in range(N_REPS):
        allp = {c: [] for c in CONJ}; directo = []
        for f, (tr, te) in enumerate(KFold(N_FOLDS, shuffle=True, random_state=rep).split(X)):
            seed = rep * 100 + f
            p = probas_fold(X.iloc[tr], Y.iloc[tr], X.iloc[te], 500, seed)
            for c in CONJ:
                allp[c].append(p[c])
            m = rf(500, seed).fit(X.iloc[tr], tipos.iloc[tr])
            directo.append(pd.DataFrame(m.predict_proba(X.iloc[te]), index=X.index[te],
                                        columns=m.classes_).reindex(columns=range(1, 10), fill_value=0))
        pr = {c: pd.concat(v).reindex(X.index) for c, v in allp.items()}
        s = scores_tipo(pr); d = pd.concat(directo).reindex(X.index)
        for nom, sc, acc in (("intersección", s, topk), ("directo", d, topk_T)):
            rank = sc.apply(lambda r: list(r.sort_values(ascending=False).index), axis=1)
            for k in (1, 2, 3):
                acc[k].append(np.mean([tipos[c] in rank[c][:k] for c in X.index]))
        # calibración y errores (intersección)
        for c in X.index:
            v = s.loc[c].sort_values(ascending=False)
            marg.append((v.iloc[0] - v.iloc[1], v.index[0] == tipos[c]))
            conf_mat[tipos[c], v.index[0]] += 1
        filasT.append({"rep": rep, "M2_interseccion": (s.idxmax(axis=1) == tipos).mean(),
                       "M2_directo": (d.idxmax(axis=1) == tipos).mean()})
    T = pd.DataFrame(filasT); T.to_csv(os.path.join(OUT, "T_quinto_clasificador.csv"), index=False)
    print("  C · top-k (el tipo real entre los k más probables) · mediana [p5–p95]")
    base = tipos.value_counts(normalize=True)
    for k in (1, 2, 3):
        print(f"    top-{k}: intersección {med(topk[k])} · directo {med(topk_T[k])} · "
              f"base «los {k} tipos más comunes» {base.iloc[:k].sum():.0%} · azar {k/9:.0%}")
    mg = pd.DataFrame(marg, columns=["margen", "acierta"])
    mg["tercil"] = pd.qcut(mg.margen, 3, labels=["margen bajo", "medio", "alto"])
    cal = mg.groupby("tercil").acierta.agg(["mean", "count"])
    print("  C · calibración — acierto según el margen entre el 1.º y el 2.º tipo:")
    for t, r in cal.iterrows():
        print(f"    {t:12} {r['mean']:.0%} (n={int(r['count'])})")
    print(f"  T · quinto clasificador: tipo directo {med(T.M2_directo)} · intersección {med(T.M2_interseccion)}"
          f" · el directo gana en {(T.M2_directo > T.M2_interseccion).sum()}/{N_REPS}, empata en "
          f"{(T.M2_directo == T.M2_interseccion).sum()}")
    # E
    # Por diseño, dos tipos distintos comparten SIEMPRE exactamente un grupo (el sistema de 9 tipos
    # en 4 tríadas es un plano afín de orden 3). No hay errores «cercanos»: lo informativo es CUÁL
    # conjunto comparten el tipo real y el predicho — el único que «acertó» en ese error.
    print("  E · en cada error, ¿qué conjunto comparten el tipo real y el predicho? (siempre es uno)")
    comp = collections.Counter()
    for t in range(1, 10):
        for p in range(1, 10):
            if t != p and conf_mat[t, p]:
                for c in CONJ:
                    if C.grupo_de(t, c) == C.grupo_de(p, c):
                        comp[C.CORTO[c]] += conf_mat[t, p]
    tot = sum(comp.values())
    for c in CORTO:
        print(f"    {c:11} {comp[c]/tot:.0%} de los errores (si fuera parejo: 25%)")
    pred = conf_mat[1:, 1:].sum(0); real = conf_mat[1:, 1:].sum(1)
    print("    predicho / real por tipo (sumado en las 20 repeticiones): " +
          " · ".join(f"{t}: {pred[t-1]}/{real[t-1]}" for t in range(1, 10)))
    cm = pd.DataFrame(conf_mat[1:, 1:], index=range(1, 10), columns=range(1, 10))
    cm.to_csv(os.path.join(OUT, "E_matriz_confusion.csv"))
    fig, axs = plt.subplots(1, 3, figsize=(17, 5))
    ks = [1, 2, 3]
    axs[0].bar([x - .2 for x in ks], [np.median(topk[k]) for k in ks], .4, label="intersección (4 RF)")
    axs[0].bar([x + .2 for x in ks], [np.median(topk_T[k]) for k in ks], .4, label="directo (RF 9 clases)")
    axs[0].plot(ks, [k / 9 for k in ks], "k--", label="azar"); axs[0].plot(ks, [base.iloc[:k].sum() for k in ks], "r:", label="tipos más comunes")
    axs[0].set_xticks(ks); axs[0].set_xticklabels(["top-1", "top-2", "top-3"]); axs[0].legend(fontsize=8)
    axs[0].set_title("C · ¿el tipo real está entre los k más probables?")
    axs[1].bar(cal.index.astype(str), cal["mean"], color="#55a868"); axs[1].axhline(1 / 9, c="k", ls="--")
    axs[1].set_title("C · calibración: acierto según la seguridad del modelo"); axs[1].set_ylim(0, 1)
    rows = cm.loc[[t for t in range(1, 10) if cm.loc[t].sum()]]
    im = axs[2].imshow((rows.T / rows.sum(axis=1)).T, cmap="Blues", vmin=0, vmax=.6)
    axs[2].set_xticks(range(9)); axs[2].set_xticklabels(range(1, 10)); axs[2].set_yticks(range(len(rows)))
    axs[2].set_yticklabels(rows.index); axs[2].set_xlabel("tipo predicho"); axs[2].set_ylabel("tipo real")
    axs[2].set_title("E · a dónde va cada tipo (fracción de la fila)"); fig.colorbar(im, ax=axs[2], shrink=.8)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "CET.png"), dpi=150); plt.close(fig)


# ─────────────────────────── L · calidad de etiquetas ───────────────────────────
def analisis_L(X, Y, tipos, conf):
    print("\n== L · Calidad de etiquetas (300 árboles, 5×20)")
    print(f"  confianza: {dict(conf.value_counts())}")
    res = []
    for nom, mask in (("todos", conf.index == conf.index), ("sin baja", conf != "baja"),
                      ("sólo alta", conf == "alta")):
        d = cv_basica(X[mask], Y[mask], tipos[mask], 300)
        base = tipos[mask].value_counts(normalize=True).iloc[0]
        bm = {c: Y[mask][c].value_counts(normalize=True).iloc[0] for c in CONJ}
        print(f"  {nom:9} n={mask.sum():2} · M2 {med(d.M2)} (base {base:.0%}) · M1 " +
              " ".join(f"{C.CORTO[c]} {np.median(d[f'M1_{C.CORTO[c]}']):.0%}/{bm[c]:.0%}" for c in CONJ))
        d["muestra"] = nom; res.append(d)
    pd.concat(res).to_csv(os.path.join(OUT, "L_calidad_etiquetas.csv"), index=False)


# ─────────────────────────── R · quitar ítems poco discriminantes ───────────────────────────
def disc_items(dfi, Y, tipos, bank):
    """Discriminación de cada ítem SOBRE LAS PERSONAS QUE SE LE PASAN (el fold de entrenamiento).
    Escenario: fracción que elige la opción de su propio grupo − 1/3.
    Likert: media de los miembros del grupo − media de los no miembros (polaridad aplicada), en desvíos."""
    out = {}
    for q in dfi.columns:
        o = bank[q]; conj = o[0]["grouping_system"]
        if o[0]["format"] == "scenario":
            elegido = np.array([o[v - 1]["group_label"] for v in dfi[q]])
            out[q] = ("scenario", (elegido == Y.loc[dfi.index, conj].values).mean() - 1 / 3)
        else:
            v = dfi[q].astype(float)
            if (o[0].get("polarity") or "").lower().startswith("inv"):
                v = 6 - v
            mem = (Y.loc[dfi.index, conj] == o[0]["group_label"]).values
            sd = v.std() or 1
            out[q] = ("likert", (v[mem].mean() - v[~mem].mean()) / sd if mem.any() and (~mem).any() else 0)
    return out


def analisis_R(dfi, X, owner, Y, tipos, bank):
    print("\n== R · Quitar los ítems que menos discriminan — adentro de cada fold (300 árboles, 5×20)")
    res = []
    for frac in (0.0, 0.25, 0.50):
        filas = []
        for rep in range(N_REPS):
            allp = {c: [] for c in CONJ}
            for f, (tr, te) in enumerate(KFold(N_FOLDS, shuffle=True, random_state=rep).split(X)):
                dsc = disc_items(dfi.iloc[tr], Y.iloc[tr], tipos.iloc[tr], bank)
                keep = set()
                for fmt in ("scenario", "likert"):
                    qs = sorted([q for q, (fm, _) in dsc.items() if fm == fmt], key=lambda q: dsc[q][1])
                    keep |= set(qs[int(len(qs) * frac):])
                cols = [c for c in X.columns if owner[c] in keep]
                p = probas_fold(X.iloc[tr][cols], Y.iloc[tr], X.iloc[te][cols], 300, rep * 100 + f)
                for c in CONJ:
                    allp[c].append(p[c])
            pr = {c: pd.concat(v).reindex(X.index) for c, v in allp.items()}
            filas.append({"rep": rep, "quitado": frac, **metricas(pr, Y, tipos)})
        d = pd.DataFrame(filas); res.append(d)
        print(f"  quitando {frac:.0%} peor de cada formato: M2 {med(d.M2)} · M1 " +
              " ".join(f"{C.CORTO[c]} {np.median(d[f'M1_{C.CORTO[c]}']):.0%}" for c in CONJ))
    pd.concat(res).to_csv(os.path.join(OUT, "R_quitar_items.csv"), index=False)


# ─────────────────────────── A · curva de aprendizaje ───────────────────────────
def analisis_A(X, Y, tipos):
    print("\n== A · Curva de aprendizaje (300 árboles; 9 personas de test por sorteo, 40 sorteos)")
    sizes = [10, 15, 20, 25, 30, 35]
    res = []
    for rep in range(40):
        rng = np.random.default_rng(1000 + rep)
        perm = rng.permutation(len(X)); te, pool = perm[:9], perm[9:]
        for n in sizes:
            tr = pool[:n]
            p = probas_fold(X.iloc[tr], Y.iloc[tr], X.iloc[te], 300, rep * 10 + n)
            res.append({"rep": rep, "n": n, **metricas(p, Y.iloc[te], tipos.iloc[te])})
    d = pd.DataFrame(res); d.to_csv(os.path.join(OUT, "A_curva_aprendizaje.csv"), index=False)
    g = d.groupby("n").mean(numeric_only=True)
    for n, r in g.iterrows():
        print(f"  n_entrenamiento={n:2}: M2 {r.M2:.0%} · M1 medio {np.mean([r[f'M1_{c}'] for c in CORTO]):.0%}")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(g.index, g.M2, "o-", label="tipo (M2)")
    ax.plot(g.index, g[[f"M1_{c}" for c in CORTO]].mean(axis=1), "s-", label="por conjunto (M1, media)")
    se = d.groupby("n").M2.std() / np.sqrt(40)
    ax.fill_between(g.index, g.M2 - 2 * se, g.M2 + 2 * se, alpha=.2)
    ax.axhline(1 / 9, c="k", ls="--", lw=.8); ax.text(sizes[0], 1 / 9 + .01, "azar tipo", fontsize=8)
    ax.axhline(1 / 3, c="grey", ls="--", lw=.8); ax.text(sizes[0], 1 / 3 + .01, "azar conjunto", fontsize=8)
    ax.set_xlabel("personas para entrenar"); ax.set_ylabel("acierto"); ax.legend()
    ax.set_title("A · Curva de aprendizaje: ¿mejora con más gente?")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "A_curva_aprendizaje.png"), dpi=150); plt.close(fig)


# ─────────────────────────── D · largo del test ───────────────────────────
def analisis_D(X, owner, Y, tipos):
    print("\n== D · Largo del test (300 árboles; 8 sorteos de ítems × 5 folds)")
    items = sorted(set(owner.values()))
    res = []
    for K in (20, 40, 60, 80, 100, 120, 145):
        for draw in range(8):
            rng = np.random.default_rng(2000 + draw * 7 + K)
            sel = set(rng.choice(items, K, replace=False))
            cols = [c for c in X.columns if owner[c] in sel]
            allp = {c: [] for c in CONJ}
            for f, (tr, te) in enumerate(KFold(N_FOLDS, shuffle=True, random_state=draw).split(X)):
                p = probas_fold(X.iloc[tr][cols], Y.iloc[tr], X.iloc[te][cols], 300, draw * 100 + f)
                for c in CONJ:
                    allp[c].append(p[c])
            pr = {c: pd.concat(v).reindex(X.index) for c, v in allp.items()}
            res.append({"K": K, "draw": draw, **metricas(pr, Y, tipos)})
    d = pd.DataFrame(res); d.to_csv(os.path.join(OUT, "D_largo_test.csv"), index=False)
    g = d.groupby("K").mean(numeric_only=True)
    for K, r in g.iterrows():
        print(f"  {K:3} ítems: M2 {r.M2:.0%} · M1 medio {np.mean([r[f'M1_{c}'] for c in CORTO]):.0%}")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(g.index, g.M2, "o-", label="tipo (M2)")
    ax.plot(g.index, g[[f"M1_{c}" for c in CORTO]].mean(axis=1), "s-", label="por conjunto (M1, media)")
    ax.axhline(1 / 9, c="k", ls="--", lw=.8); ax.axhline(1 / 3, c="grey", ls="--", lw=.8)
    ax.set_xlabel("ítems respondidos"); ax.set_ylabel("acierto"); ax.legend()
    ax.set_title("D · ¿Cuánto acierta según el largo del test?")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "D_largo_test.png"), dpi=150); plt.close(fig)


# ─────────────────────────── B · techo por simulación ───────────────────────────
def analisis_B(dfi, bank, tipos):
    print("\n== B · Techo por simulación (personas sintéticas; 300 árboles; 1800 entrenan, 900 prueban)")
    items = list(dfi.columns)
    K = {q: (3 if bank[q][0]["format"] == "scenario" else 5) for q in items}
    presentes = sorted(tipos.unique())
    res = []
    for etiqueta in ("reales", "permutadas"):
        for m in (0, 5, 20):
            rng = np.random.default_rng(3000 + m)
            t_obs = tipos.values if etiqueta == "reales" else rng.permutation(tipos.values)
            P = {}
            for q in items:
                v = dfi[q].values; k = K[q]
                glob = np.bincount(v - 1, minlength=k) / len(v)
                for t in presentes:
                    c = np.bincount(v[t_obs == t] - 1, minlength=k)
                    P[(q, t)] = (c + m * glob + 1e-9) / (c.sum() + m * glob.sum() + k * 1e-9)

            def generar(n):
                ts = rng.choice(presentes, n)
                rows = {q: [rng.choice(K[q], p=P[(q, t)]) + 1 for t in ts] for q in items}
                return pd.DataFrame(rows), pd.Series(ts)
            dtr, ttr = generar(1800); dte, tte = generar(900)
            Xtr, _ = codificar(dtr.astype(str), bank); Xte, _ = codificar(dte.astype(str), bank)
            Ytr = pd.DataFrame({c: [C.grupo_de(t, c) for t in ttr] for c in CONJ})
            Yte = pd.DataFrame({c: [C.grupo_de(t, c) for t in tte] for c in CONJ})
            p = probas_fold(Xtr, Ytr, Xte, 300, m)
            met = metricas(p, Yte, tte)
            # Bayes ingenuo con las probabilidades verdaderas del generador: el óptimo de ese mundo
            logp = np.zeros((len(dte), len(presentes)))
            for j, t in enumerate(presentes):
                for q in items:
                    logp[:, j] += np.log(P[(q, t)][dte[q].values - 1])
            met["M2_bayes_optimo"] = (np.array(presentes)[logp.argmax(1)] == tte.values).mean()
            res.append({"etiquetas": etiqueta, "suavizado_m": m, **met})
            print(f"  etiquetas {etiqueta:10} m={m:2}: RF tipo {met['M2']:.0%} · óptimo bayesiano {met['M2_bayes_optimo']:.0%}"
                  f" · M1 " + " ".join(f"{c} {met[f'M1_{c}']:.0%}" for c in CORTO))
    pd.DataFrame(res).to_csv(os.path.join(OUT, "B_techo_simulacion.csv"), index=False)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); return 2
    solo = set(sys.argv[sys.argv.index("--solo") + 1].split(",")) if "--solo" in sys.argv else set("CLRADB")
    os.makedirs(OUT, exist_ok=True)
    bank, dfi, X, owner, Y, tipos, conf = cargar(args[0])
    print(f"{len(X)} respondentes · {X.shape[1]} columnas")
    t0 = time.time()
    for k, fn in (("C", lambda: analisis_CET(X, Y, tipos)), ("L", lambda: analisis_L(X, Y, tipos, conf)),
                  ("R", lambda: analisis_R(dfi, X, owner, Y, tipos, bank)), ("A", lambda: analisis_A(X, Y, tipos)),
                  ("D", lambda: analisis_D(X, owner, Y, tipos)), ("B", lambda: analisis_B(dfi, bank, tipos))):
        if k in solo:
            fn(); print(f"  ({(time.time() - t0) / 60:.0f} min)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
