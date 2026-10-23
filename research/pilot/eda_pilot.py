# -*- coding: utf-8 -*-
"""Análisis exploratorio del piloto, previo al entrenamiento.

    python eda_pilot.py responses_wide.csv

Dos partes, con dos puntos de vista distintos:

PARTE I · EL BANCO (vista del diseño — insumo del backlog)
  Mira cada grupo como una escala propia: los ítems escritos para él.
  I.1  consistencia interna de las subescalas Likert (alfa) y correlación ítem-resto
  I.2  multirrasgo-multimétodo: el mismo grupo medido por escenario y por Likert
  I.3  sesgo de posición en los escenarios

PARTE II · EL CLASIFICADOR (vista del modelo — insumo del documento y del MVP)
  Mira el vector completo, tal como lo recibe cada Random Forest: 145 ítems codificados como en
  `train_pilot.py` (escenarios one-hot, Likert 1–5), sin partir por el grupo para el que se
  escribió cada ítem. `group_label` no se usa para calcular nada; sólo se usa al final para
  ANOTAR si un ítem con señal es del conjunto o de otro (lo que el PDR llama hallazgo «off-system»).
  II.1 estructura sin etiquetas: componentes principales y análisis paralelo de Horn
  II.2 mapa de respondentes en el plano de las dos primeras componentes, pintado por etiqueta
  II.3 agrupamiento sin etiquetas (k-means) contra tipo y conjuntos — ARI
  II.4 señal global: ¿se parecen más entre sí las personas con la misma etiqueta? (PERMANOVA)
  II.5 mapa ítem × clasificador: asociación de cada ítem con cada uno de los 4 objetivos, contra
       un nulo por permutación, con control de falsos descubrimientos (Benjamini-Hochberg)
  II.6 estilo de respuesta por persona (aquiescencia, punto medio, extremos, concentración)

REGLA DE USO. Lo que no usa etiquetas (I.*, II.1, II.6) puede informar decisiones de modelo.
Lo que sí las usa (II.2–II.5) es descriptivo: cualquier decisión de modelo que salga de ahí va como
enmienda al §6 ter del plan y se compara contra la corrida registrada.

Muestra: los respondentes con `tipo_asignado`, sin excepciones (igual que el entrenamiento).
Figuras en eda_out/. Semilla fija: 0.
"""
import os, sys, collections, warnings
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

import contrast as C
from pilot_metrics import con_copias

warnings.filterwarnings("ignore")
HERE = C.DATA   # datos y salidas, fuera del repositorio (ver README)
OUT = os.path.join(HERE, "eda_out")
SEED = 0
N_PERM = 2000
CONJ = list(C.GRUPOS)
COLOR_T = {1: "#1f77b4", 2: "#ff7f0e", 3: "#2ca02c", 4: "#d62728", 5: "#9467bd",
           6: "#8c564b", 7: "#e377c2", 8: "#7f7f7f", 9: "#17becf"}


# ───────────────────────────── carga ─────────────────────────────
def cargar(path):
    bank, B, _ = con_copias()
    df = pd.read_csv(path, dtype=str).set_index("respondent_id")
    items = [c for c in df.columns if c.startswith("Q")]
    df = df[[bool(B.get(c) and B[c].get("tipo_asignado")) for c in df.index]]
    X = df[items].astype(int)
    tipos = pd.Series({c: int(B[c]["tipo_asignado"]) for c in X.index})
    Y = pd.DataFrame({C.CORTO[c]: [C.grupo_de(t, c) for t in tipos] for c in CONJ}, index=X.index)
    fmt = {q: bank[q][0]["format"] for q in items}
    return bank, X, tipos, Y, fmt


def codificar(X, bank, fmt):
    """Igual que train_pilot.codificar: escenarios one-hot, Likert entero 1–5."""
    cols = {}
    for q in X.columns:
        if fmt[q] == "scenario":
            for k in range(1, len(bank[q]) + 1):
                cols[f"{q}_o{k}"] = (X[q] == k).astype(int)
        else:
            cols[q] = X[q]
    return pd.DataFrame(cols, index=X.index)


def estandarizar(M):
    M = M.astype(float)
    sd = M.std(ddof=0).replace(0, 1)
    return (M - M.mean()) / sd


# ───────────────────────────── PARTE I ─────────────────────────────
def parte_I(bank, X, fmt):
    print("=" * 76 + "\nPARTE I · EL BANCO (vista del diseño)\n" + "=" * 76)
    lik = collections.defaultdict(dict)
    for q in X.columns:
        o = bank[q][0]
        if fmt[q] != "likert":
            continue
        v = X[q] if not (o.get("polarity") or "").lower().startswith("inv") else 6 - X[q]
        lik[f"{C.CORTO[o['grouping_system']]}·{o['group_label']}"][q] = v

    def alpha(m):
        k = m.shape[1]
        return k / (k - 1) * (1 - m.var(ddof=1).sum() / m.sum(axis=1).var(ddof=1))

    print("\nI.1 · Alfa de Cronbach por subescala Likert · correlación ítem-resto")
    al, ir = {}, []
    for g in sorted(lik):
        m = pd.DataFrame(lik[g])
        al[g] = alpha(m)
        for q in m:
            r = np.corrcoef(m[q], m.drop(columns=q).sum(axis=1))[0, 1]
            ir.append((g, q, r))
        neg = [f"{q} {r:+.2f}" for gg, q, r in ir if gg == g and r < 0]
        print(f"  {g:24} k={m.shape[1]}  α={al[g]:+.2f}" + (f"   negativos: {', '.join(neg)}" if neg else ""))

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1, 1.2]})
    gs = sorted(al, key=al.get)
    a1.barh(gs, [al[g] for g in gs], color="#4c72b0")
    a1.axvline(.70, ls="--", c="grey"); a1.text(.71, 0, "convención .70", fontsize=8, color="grey")
    a1.set_xlabel("α de Cronbach"); a1.set_title("Consistencia interna de las subescalas Likert")
    for i, g in enumerate(gs):
        rs = [r for gg, _, r in ir if gg == g]
        a2.scatter(rs, [i] * len(rs), c=["#c44e52" if r < 0 else "#4c72b0" for r in rs], s=30)
    a2.set_yticks(range(len(gs))); a2.set_yticklabels(gs); a2.axvline(0, c="grey")
    a2.set_xlabel("correlación ítem-resto"); a2.set_title("Cada ítem contra el resto de su subescala")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "I1_alfa_item_resto.png"), dpi=150); plt.close(fig)

    print("\nI.2 · Multirrasgo-multimétodo (Spearman, escenario × Likert)")
    sc = collections.defaultdict(lambda: pd.Series(0.0, index=X.index)); n_sc = collections.Counter()
    for q in X.columns:
        if fmt[q] != "scenario":
            continue
        cj = C.CORTO[bank[q][0]["grouping_system"]]; n_sc[cj] += 1
        for k, row in enumerate(bank[q], 1):
            sc[f"{cj}·{row['group_label']}"] += (X[q] == k)
    S = pd.DataFrame({g: v / n_sc[g.split("·")[0]] for g, v in sc.items()})
    L = pd.DataFrame({g: pd.DataFrame(d).mean(axis=1) for g, d in lik.items()})
    keys = sorted(L.columns)
    mt = pd.DataFrame([[S[a].rank().corr(L[b].rank()) for b in keys] for a in keys], index=keys, columns=keys)
    conv = np.diag(mt.values)
    mismo = [mt.loc[a, b] for a in keys for b in keys if a != b and a.split("·")[0] == b.split("·")[0]]
    otro = [mt.loc[a, b] for a in keys for b in keys if a.split("·")[0] != b.split("·")[0]]
    cf = sum(all(mt.loc[k, k] > mt.loc[k, b] for b in keys if b != k) and
             all(mt.loc[k, k] > mt.loc[a, k] for a in keys if a != k) for k in keys)
    for k in keys:
        print(f"  {k:24} convergente {mt.loc[k, k]:+.2f}")
    print(f"  media convergente {conv.mean():+.2f} · heterorrasgo mismo conjunto {np.mean(mismo):+.2f}"
          f" · otro conjunto {np.mean(otro):+.2f} · Campbell-Fiske {cf}/12")
    fig, ax = plt.subplots(figsize=(9, 8))
    im = ax.imshow(mt.values, cmap="RdBu_r", vmin=-.6, vmax=.6)
    ax.set_xticks(range(12)); ax.set_xticklabels(keys, rotation=90, fontsize=8)
    ax.set_yticks(range(12)); ax.set_yticklabels(keys, fontsize=8)
    for i in range(12):
        ax.add_patch(plt.Rectangle((i - .5, i - .5), 1, 1, fill=False, lw=2, ec="black"))
        ax.text(i, i, f"{mt.values[i, i]:+.2f}", ha="center", va="center", fontsize=7)
    ax.set_xlabel("Likert (media del grupo)"); ax.set_ylabel("Escenario (fracción elegida)")
    ax.set_title("Multirrasgo-multimétodo · diagonal = validez convergente")
    fig.colorbar(im, ax=ax, shrink=.8); fig.tight_layout()
    fig.savefig(os.path.join(OUT, "I2_mtmm.png"), dpi=150); plt.close(fig)

    print("\nI.3 · Sesgo de posición (escenarios)")
    sce = [q for q in X.columns if fmt[q] == "scenario"]
    pos = np.array([(X[sce] == k).values.sum() for k in (1, 2, 3)])
    per = pd.concat([(X[sce] == k).mean(axis=1) for k in (1, 2, 3)], axis=1)
    print(f"  posiciones 1/2/3: {', '.join(f'{p / pos.sum():.1%}' for p in pos)}")
    # test por persona: la fracción de posición 1 de cada persona contra 1/3 (signos)
    from scipy.stats import binomtest
    up = int((per[0] > 1 / 3).sum())
    print(f"  por persona: {up}/{len(per)} eligen la posición 1 más de 1/3 · signos p={binomtest(up, len(per), .5, alternative='greater').pvalue:.3f}")
    print(f"  personas con una posición >50%: {[c for c in per.index if per.loc[c].max() > .5]}")


# ───────────────────────────── PARTE II ─────────────────────────────
def pseudo_F(D2, lab):
    """PERMANOVA (Anderson 2001) sobre distancias al cuadrado."""
    N = len(lab); grupos = np.unique(lab); a = len(grupos)
    sst = D2[np.triu_indices(N, 1)].sum() / N
    ssw = 0.0
    for g in grupos:
        i = np.where(lab == g)[0]
        if len(i) > 1:
            ssw += D2[np.ix_(i, i)][np.triu_indices(len(i), 1)].sum() / len(i)
    return ((sst - ssw) / (a - 1)) / (ssw / (N - a)), 1 - ssw / sst


def permanova(Z, lab, rng):
    D2 = ((Z[:, None, :] - Z[None, :, :]) ** 2).sum(-1)
    f0, r2 = pseudo_F(D2, lab)
    k = sum(pseudo_F(D2, rng.permutation(lab))[0] >= f0 for _ in range(N_PERM))
    return f0, r2, (k + 1) / (N_PERM + 1)


def chi2_bloques(Oh, owners, G):
    """χ² de cada ítem contra la etiqueta, para todos los ítems a la vez.
    Oh: n × columnas one-hot (todas las opciones de todos los ítems); G: n × clases one-hot."""
    obs = Oh.T @ G                                   # columnas × clases
    out = np.zeros(len(owners))
    for j, idx in enumerate(owners):
        o = obs[idx]
        o = o[o.sum(1) > 0]
        e = o.sum(1, keepdims=True) * o.sum(0, keepdims=True) / o.sum()
        out[j] = ((o - e) ** 2 / np.where(e == 0, 1, e)).sum()
    return out


def bh(p):
    p = np.asarray(p); o = np.argsort(p); m = len(p)
    q = np.empty(m); q[o] = np.minimum.accumulate((p[o] * m / np.arange(1, m + 1))[::-1])[::-1]
    return np.minimum(q, 1)


def parte_II(bank, X, tipos, Y, fmt):
    print("\n" + "=" * 76 + "\nPARTE II · EL CLASIFICADOR (vector completo)\n" + "=" * 76)
    rng = np.random.default_rng(SEED)
    M = codificar(X, bank, fmt)
    Z = estandarizar(M).values
    sce_cols = [c for c in M.columns if "_o" in c]; lik_cols = [c for c in M.columns if "_o" not in c]
    bloques = {"todo": Z, "escenario": estandarizar(M[sce_cols]).values,
               "Likert": estandarizar(M[lik_cols]).values}
    print(f"{len(X)} respondentes · {M.shape[1]} columnas · tipos "
          + " · ".join(f"{t}×{n}" for t, n in sorted(tipos.value_counts().items())))

    # II.1 · análisis paralelo
    print("\nII.1 · Estructura sin etiquetas — componentes principales vs. ruido (Horn, 200 perm., p95)")
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, (nom, Zb) in zip(axs, bloques.items()):
        ev = np.linalg.svd(Zb, compute_uv=False) ** 2 / (len(Zb) - 1)
        null = np.array([np.linalg.svd(np.column_stack([rng.permutation(c) for c in Zb.T]),
                                       compute_uv=False) ** 2 / (len(Zb) - 1) for _ in range(200)])
        p95 = np.percentile(null, 95, axis=0)
        k = int(np.argmax(ev <= p95)) if (ev <= p95).any() else len(ev)
        var = ev / ev.sum()
        print(f"  {nom:9} componentes sobre el ruido: {k} · PC1 explica {var[0]:.1%} (ruido p95 "
              f"{p95[0] / ev.sum():.1%}) · PC1+PC2 {var[:2].sum():.1%}")
        r = np.arange(1, 16)
        ax.plot(r, ev[:15], "o-", label="observado"); ax.plot(r, p95[:15], "s--", c="grey", label="ruido p95")
        ax.set_title(f"{nom} · {k} comp. sobre el ruido"); ax.set_xlabel("componente"); ax.legend()
    axs[0].set_ylabel("autovalor")
    fig.suptitle("Análisis paralelo de Horn — ¿cuántas dimensiones reales tiene el dato?")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "II1_analisis_paralelo.png"), dpi=150); plt.close(fig)

    # II.2 · mapa
    U, s, _ = np.linalg.svd(Z - Z.mean(0), full_matrices=False)
    P = U[:, :2] * s[:2]
    fig, axs = plt.subplots(1, 5, figsize=(24, 5))
    for t in sorted(tipos.unique()):
        i = (tipos == t).values
        axs[0].scatter(P[i, 0], P[i, 1], c=COLOR_T[t], label=f"tipo {t}", s=45, ec="k", lw=.3)
    axs[0].legend(fontsize=7, ncol=2); axs[0].set_title("por tipo")
    cmap = ["#4c72b0", "#dd8452", "#55a868"]
    for ax, cj in zip(axs[1:], Y.columns):
        for j, g in enumerate(sorted(Y[cj].unique())):
            i = (Y[cj] == g).values
            ax.scatter(P[i, 0], P[i, 1], c=cmap[j], label=g, s=45, ec="k", lw=.3)
        ax.legend(fontsize=8); ax.set_title(f"por {cj}")
    for ax in axs:
        ax.set_xlabel("PC1"); ax.set_xticks([]); ax.set_yticks([])
    axs[0].set_ylabel("PC2")
    fig.suptitle("Respondentes en el plano de las dos primeras componentes (vector completo, sin etiquetas)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "II2_mapa_respondentes.png"), dpi=150); plt.close(fig)
    print("\nII.2 · Mapa de respondentes → eda_out/II2_mapa_respondentes.png")

    # II.3 · k-means
    print("\nII.3 · Agrupamiento sin etiquetas (k-means, 50 inicios) contra las etiquetas — ARI")
    for nom, lab, k in [("tipo", tipos.values, 9)] + [(c, Y[c].values, 3) for c in Y.columns]:
        km = KMeans(k, n_init=50, random_state=SEED).fit_predict(Z)
        a = adjusted_rand_score(lab, km)
        null = [adjusted_rand_score(rng.permutation(lab), km) for _ in range(N_PERM)]
        p = (sum(x >= a for x in null) + 1) / (N_PERM + 1)
        print(f"  {nom:11} k={k}  ARI={a:+.3f}  (nulo p95 {np.percentile(null, 95):+.3f})  p={p:.3f}")

    # II.4 · PERMANOVA
    print(f"\nII.4 · Señal global — PERMANOVA ({N_PERM} perm.): ¿la etiqueta explica distancia entre personas?")
    print(f"  {'objetivo':11}" + "".join(f"{b:>26}" for b in bloques))
    for nom, lab in [("tipo", tipos.values)] + [(c, Y[c].values) for c in Y.columns]:
        celdas = []
        for Zb in bloques.values():
            f, r2, p = permanova(Zb, lab, rng)
            celdas.append(f"R²={r2:.3f} F={f:.2f} p={p:.3f}")
        print(f"  {nom:11}" + "".join(f"{x:>26}" for x in celdas))

    # II.5 · ítem × clasificador
    print(f"\nII.5 · Ítem × clasificador — χ² de cada ítem contra cada objetivo, nulo por permutación ({N_PERM})")
    items = list(X.columns)
    oh, owners, j = [], [], 0
    for q in items:
        k = 3 if fmt[q] == "scenario" else 5
        for o in range(1, k + 1):
            oh.append((X[q] == o).astype(int).values)
        owners.append(list(range(j, j + k))); j += k
    Oh = np.column_stack(oh)
    filas, heat = [], np.zeros((len(items), len(Y.columns)))
    for c_i, cj in enumerate(Y.columns):
        clases = sorted(Y[cj].unique())
        G = np.column_stack([(Y[cj] == g).astype(int).values for g in clases])
        obs = chi2_bloques(Oh, owners, G)
        null = np.array([chi2_bloques(Oh, owners, G[rng.permutation(len(G))]) for _ in range(N_PERM)])
        p = ((null >= obs).sum(0) + 1) / (N_PERM + 1)
        q = bh(p)
        fwer = np.percentile(null.max(1), 95)
        heat[:, c_i] = -np.log10(p)
        for i, it in enumerate(items):
            filas.append({"item": it, "formato": fmt[it], "clasificador": cj,
                          "conjunto_del_item": C.CORTO[bank[it][0]["grouping_system"]],
                          "chi2": obs[i], "p": p[i], "q_BH": q[i]})
        own = np.array([C.CORTO[bank[it][0]["grouping_system"]] == cj for it in items])
        sig = q < .10
        print(f"  {cj:11} p<.05: {int((p < .05).sum()):3} (esperados {.05 * len(items):.1f}) · "
              f"q_BH<.10: {int(sig.sum()):2} · sobre el máximo del nulo: {int((obs > fwer).sum())}"
              f" · de los p<.05, del propio conjunto: {int(((p < .05) & own).sum())}/{int((p < .05).sum())}"
              f" (proporción de base {own.mean():.0%})")
    res = pd.DataFrame(filas)
    res.to_csv(os.path.join(OUT, "II5_item_x_clasificador.csv"), index=False)
    top = res.sort_values("p").head(12)
    print("  los 12 más asociados (cualquier clasificador):")
    for _, r in top.iterrows():
        tag = "propio" if r.conjunto_del_item == r.clasificador else f"de {r.conjunto_del_item}"
        print(f"    {r['item']} ({r.formato[:3]}, {tag:15}) → {r.clasificador:11} p={r.p:.4f} q={r.q_BH:.2f}")
    fig, ax = plt.subplots(figsize=(16, 4))
    im = ax.imshow(heat.T, aspect="auto", cmap="magma_r", vmin=0, vmax=3)
    ax.set_yticks(range(len(Y.columns))); ax.set_yticklabels(Y.columns)
    ax.set_xticks(range(0, len(items), 5)); ax.set_xticklabels(items[::5], rotation=90, fontsize=7)
    ax.set_title("Asociación de cada ítem con cada clasificador · −log10(p) por permutación · 1.3 ≈ p .05, 3 = p .001")
    fig.colorbar(im, ax=ax, shrink=.8); fig.tight_layout()
    fig.savefig(os.path.join(OUT, "II5_heatmap_item_clasificador.png"), dpi=150); plt.close(fig)
    fig, axs = plt.subplots(1, 4, figsize=(16, 3.8), sharey=True)
    for ax, cj in zip(axs, Y.columns):
        pv = np.sort(res[res.clasificador == cj].p.values)
        ax.plot(np.arange(1, len(pv) + 1) / len(pv), pv, ".", ms=3); ax.plot([0, 1], [0, 1], c="grey", ls="--")
        ax.set_title(cj); ax.set_xlabel("cuantil esperado (uniforme)")
    axs[0].set_ylabel("p observado (ordenado)")
    fig.suptitle("Distribución de p de los 145 ítems por clasificador · sobre la diagonal = ruido, debajo = señal")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "II5_qq_p.png"), dpi=150); plt.close(fig)

    # II.6 · estilo
    print("\nII.6 · Estilo de respuesta por persona (Likert crudo, sin invertir)")
    lk = X[[q for q in items if fmt[q] == "likert"]]
    est = pd.DataFrame({
        "aquiescencia": lk.mean(axis=1),
        "punto_medio": (lk == 3).mean(axis=1),
        "extremos": lk.isin([1, 5]).mean(axis=1),
        "concentracion": lk.apply(lambda r: r.value_counts().iloc[0] / len(r), axis=1)})
    est["tipo"] = tipos
    est.to_csv(os.path.join(OUT, "II6_estilo.csv"))
    print("  " + " · ".join(f"{c} mediana {est[c].median():.2f} [{est[c].min():.2f}–{est[c].max():.2f}]"
                            for c in est.columns[:-1]))
    print("  correlaciones entre índices (Spearman):")
    print(est.iloc[:, :-1].corr("spearman").round(2).to_string().replace("\n", "\n    "))
    fig, axs = plt.subplots(1, 4, figsize=(16, 4))
    ts = sorted(tipos.unique())
    for ax, c in zip(axs, est.columns[:-1]):
        ax.boxplot([est[est.tipo == t][c] for t in ts], tick_labels=[str(t) for t in ts])
        for i, t in enumerate(ts, 1):
            v = est[est.tipo == t][c]
            ax.scatter(np.full(len(v), i) + rng.uniform(-.12, .12, len(v)), v, s=12, c=COLOR_T[t], zorder=3)
        ax.set_title(c); ax.set_xlabel("tipo")
    fig.suptitle("Estilo de respuesta Likert por tipo (el tipo sólo agrupa la vista; los índices no lo usan)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "II6_estilo_por_tipo.png"), dpi=150); plt.close(fig)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); return 2
    os.makedirs(OUT, exist_ok=True)
    bank, X, tipos, Y, fmt = cargar(args[0])
    parte_I(bank, X, fmt)
    parte_II(bank, X, tipos, Y, fmt)
    print(f"\nFiguras en {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
