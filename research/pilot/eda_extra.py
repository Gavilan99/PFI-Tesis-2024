# -*- coding: utf-8 -*-
"""Análisis exploratorio complementario (rápido, sin entrenar modelos).

    python eda_extra.py responses_wide.csv

  X1  discriminación por ítem: distribución, y si el ranking de ítems es estable o es ruido
  X2  quitar ítems poco discriminantes con el heurístico modal: adentro del fold vs. «la trampa»
  X3  acierto del heurístico modal según la confianza de la etiqueta
  X4  sesgo de posición y cansancio a lo largo del orden real de administración
  X5  qué representan PC1 y PC2, y quiénes son los respondentes aislados
  X6  escenario vs. Likert con una misma vara (AUC por ítem)
  X7  factibilidad del 80%: qué discriminación por ítem y cuántos ítems harían falta

Figuras en eda_out/. Semilla fija: 0.
"""
import os, sys, re, csv, io, collections, warnings
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import binomtest, mannwhitneyu

import contrast as C
from pilot_metrics import con_copias
from eda_pilot import cargar, codificar, estandarizar

warnings.filterwarnings("ignore")
HERE = C.DATA   # datos y salidas, fuera del repositorio (ver README)
OUT = os.path.join(HERE, "eda_out")
EXPORT = os.path.join(HERE, "NureonAI — Cuestionario de personalidad.csv")
CONJ = list(C.GRUPOS)
rng = np.random.default_rng(0)


def own_matrix(bank, X, Y):
    """Para cada escenario y persona: 1 si eligió la opción de su propio grupo."""
    sce = [q for q in X.columns if bank[q][0]["format"] == "scenario"]
    M = pd.DataFrame(index=X.index)
    for q in sce:
        cj = C.CORTO[bank[q][0]["grouping_system"]]
        lab = np.array([bank[q][v - 1]["group_label"] for v in X[q]])
        M[q] = (lab == Y[cj].values).astype(int)
    return M


def modal_ok(bank, X, Y, personas, items):
    """Acierto del heurístico modal por conjunto, usando sólo `items`."""
    ok, tot = 0, 0
    for conj in CONJ:
        cj = C.CORTO[conj]
        qs = [q for q in items if bank[q][0]["grouping_system"] == conj]
        for p in personas:
            cnt = collections.Counter(bank[q][X.at[p, q] - 1]["group_label"] for q in qs)
            m = max(cnt.values()); tops = [g for g in cnt if cnt[g] == m]
            ok += tops == [Y.at[p, cj]]; tot += 1
    return ok / tot


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "responses_wide.csv"
    bank, X, tipos, Y, fmt = cargar(path)
    _, B, _ = con_copias()
    conf = pd.Series({c: (B[c].get("confianza") or "").strip() for c in X.index})
    own = own_matrix(bank, X, Y)
    sce = list(own.columns)
    n = len(X)

    # X1
    print("== X1 · Discriminación por ítem (escenarios: fracción que elige su propio grupo)")
    r = own.mean()
    print(f"  media {r.mean():.1%} · desvío {r.std():.1%} · mín {r.min():.0%} ({r.idxmin()}) · "
          f"p10 {r.quantile(.1):.0%} · mediana {r.median():.0%} · p90 {r.quantile(.9):.0%} · máx {r.max():.0%} ({r.idxmax()})")
    sd0 = np.sqrt(1 / 3 * 2 / 3 / n)
    print(f"  desvío esperable si TODOS los ítems discriminaran igual (sólo ruido de muestreo): {sd0:.1%}")
    cors = []
    for _ in range(500):
        perm = rng.permutation(n); a, b = perm[:n // 2], perm[n // 2:]
        cors.append(np.corrcoef(own.iloc[a].mean(), own.iloc[b].mean())[0, 1])
    print(f"  estabilidad del ranking: correlación entre la discriminación medida en dos mitades de la muestra "
          f"= {np.mean(cors):+.2f} (500 particiones; 1 = ranking estable, 0 = ranking al azar)")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.2))
    _, edges, _ = a1.hist(r, bins=15, color="#4c72b0", ec="w"); a1.axvline(1 / 3, c="k", ls="--", label="azar 33%")
    xs = np.linspace(r.min() - .05, r.max() + .05, 200); bw = edges[1] - edges[0]
    a1.plot(xs, len(r) * bw * np.exp(-(xs - r.mean()) ** 2 / (2 * sd0 ** 2)) / (sd0 * np.sqrt(2 * np.pi)),
            c="#c44e52", label="si todos discriminaran igual (sólo ruido)")
    a1.set_xlabel("fracción que elige su propio grupo"); a1.set_ylabel("ítems"); a1.legend(fontsize=8)
    a1.set_title("X1 · Discriminación de los 96 escenarios")
    a2.hist(cors, bins=30, color="#55a868", ec="w"); a2.axvline(0, c="k", ls="--")
    a2.set_title("X1 · ¿El ranking de ítems se repite en otra mitad de la gente?")
    a2.set_xlabel("correlación mitad A vs. mitad B")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "X1_discriminacion_items.png"), dpi=150); plt.close(fig)

    # X2
    print("\n== X2 · Quitar los escenarios menos discriminantes (heurístico modal, 5 folds × 20)")
    from sklearn.model_selection import KFold
    for frac in (0, .25, .5):
        honest, leak = [], []
        rk_all = r.sort_values()
        keep_leak = list(rk_all.index[int(len(sce) * frac):])
        for rep in range(20):
            for tr, te in KFold(5, shuffle=True, random_state=rep).split(X):
                rk = own.iloc[tr].mean().sort_values()
                keep = list(rk.index[int(len(sce) * frac):])
                honest.append(modal_ok(bank, X, Y, X.index[te], keep))
                leak.append(modal_ok(bank, X, Y, X.index[te], keep_leak))
        print(f"  quitando {frac:.0%}: honesto (ranking con el fold de entrenamiento) {np.mean(honest):.1%} · "
              f"trampa (ranking con todos, incluido el test) {np.mean(leak):.1%}")

    # X3
    print("\n== X3 · Heurístico modal según la confianza de la etiqueta (escenarios, por conjunto)")
    for c in ("alta", "media", "baja"):
        ps = conf.index[conf == c]
        if len(ps):
            print(f"  {c:5} n={len(ps):2}: {modal_ok(bank, X, Y, ps, sce):.0%}")

    # X4
    print("\n== X4 · Posición y cansancio a lo largo del orden real del formulario")
    h = next(csv.reader(io.open(EXPORT, encoding="utf-8")))
    orden = [re.match(r"(Q\d{3})", x).group(1) for x in h if re.match(r"Q\d{3}", x)]
    pag = {q: i // 20 + 1 for i, q in enumerate(orden)}
    filas = []
    for p in range(1, max(pag.values()) + 1):
        qs = [q for q in orden if pag[q] == p]
        s = [q for q in qs if fmt[q] == "scenario"]; l = [q for q in qs if fmt[q] == "likert"]
        lk = X[l]
        filas.append({"pagina": p, "esc": len(s), "lik": len(l),
                      "pos1": (X[s] == 1).values.mean(), "pos2": (X[s] == 2).values.mean(), "pos3": (X[s] == 3).values.mean(),
                      "propio": own[s].values.mean(), "lik_medio": (lk == 3).values.mean(),
                      "lik_extremos": lk.isin([1, 5]).values.mean()})
    F = pd.DataFrame(filas).set_index("pagina")
    print(F.round(3).to_string())
    mitad = len(orden) // 2
    s1 = [q for q in orden[:mitad] if fmt[q] == "scenario"]; s2 = [q for q in orden[mitad:] if fmt[q] == "scenario"]
    l1 = [q for q in orden[:mitad] if fmt[q] == "likert"]; l2 = [q for q in orden[mitad:] if fmt[q] == "likert"]
    for nom, a, b in (("propio grupo (escenarios)", own[s1].mean(axis=1), own[s2].mean(axis=1)),
                      ("posición 1 (escenarios)", (X[s1] == 1).mean(axis=1), (X[s2] == 1).mean(axis=1)),
                      ("punto medio (Likert)", (X[l1] == 3).mean(axis=1), (X[l2] == 3).mean(axis=1))):
        d = b - a; up = int((d > 0).sum()); dn = int((d < 0).sum())
        p = binomtest(up, up + dn, .5).pvalue if up + dn else 1
        print(f"  {nom:26} 1.ª mitad {a.mean():.1%} → 2.ª mitad {b.mean():.1%} · suben {up}, bajan {dn} · signos p={p:.2f}")
    fig, axs = plt.subplots(1, 3, figsize=(16, 4.2))
    for k, c in zip((1, 2, 3), ("#4c72b0", "#dd8452", "#55a868")):
        axs[0].plot(F.index, F[f"pos{k}"], "o-", c=c, label=f"posición {k}")
    axs[0].axhline(1 / 3, c="k", ls="--"); axs[0].set_title("X4 · Posición elegida por página"); axs[0].legend(fontsize=8)
    axs[1].plot(F.index, F.propio, "o-", c="#c44e52"); axs[1].axhline(1 / 3, c="k", ls="--")
    axs[1].set_title("X4 · ¿Se elige el propio grupo menos al final?")
    axs[2].plot(F.index, F.lik_medio, "o-", label="punto medio (3)"); axs[2].plot(F.index, F.lik_extremos, "s-", label="extremos (1 o 5)")
    axs[2].set_title("X4 · Estilo Likert por página"); axs[2].legend(fontsize=8)
    for ax in axs:
        ax.set_xlabel("página del formulario (20 ítems c/u)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "X4_cansancio.png"), dpi=150); plt.close(fig)

    # X5
    print("\n== X5 · Qué representan PC1 y PC2")
    M = codificar(X, bank, fmt); Z = estandarizar(M)
    U, s, Vt = np.linalg.svd(Z.values - Z.values.mean(0), full_matrices=False)
    P = pd.DataFrame(U[:, :2] * s[:2], index=X.index, columns=["PC1", "PC2"])
    lik = [q for q in X.columns if fmt[q] == "likert"]
    est = pd.DataFrame({"aquiescencia": X[lik].mean(axis=1), "punto_medio": (X[lik] == 3).mean(axis=1),
                        "extremos": X[lik].isin([1, 5]).mean(axis=1),
                        "pos1": (X[sce] == 1).mean(axis=1)})
    for pc in ("PC1", "PC2"):
        print(f"  {pc}: correlación con " + " · ".join(f"{c} {P[pc].corr(est[c], method='spearman'):+.2f}" for c in est))
        load = pd.Series(Vt[0 if pc == "PC1" else 1], index=M.columns)
        top = load.abs().sort_values(ascending=False).head(8).index
        print(f"    columnas que más pesan: " + ", ".join(f"{c} {load[c]:+.2f}" for c in top))
    izq = P.PC1.sort_values().head(4)
    print("  los 4 más a la izquierda de PC1: " + ", ".join(
        f"{c} (tipo {tipos[c]}, PC1 {v:.1f}, aquiescencia {est.at[c,'aquiescencia']:.2f}, medio {est.at[c,'punto_medio']:.0%}, extremos {est.at[c,'extremos']:.0%})"
        for c, v in izq.items()))

    # X6
    print("\n== X6 · Escenario vs. Likert con la misma vara: AUC del ítem para reconocer a los miembros de su grupo")
    from sklearn.metrics import roc_auc_score
    auc = {}
    for q in X.columns:
        o = bank[q]; cj = C.CORTO[o[0]["grouping_system"]]
        if fmt[q] == "scenario":
            vals = []
            for g in C.GRUPOS[o[0]["grouping_system"]]:
                eleg = np.array([o[v - 1]["group_label"] == g for v in X[q]]).astype(int)
                mem = (Y[cj] == g).astype(int).values
                if 0 < mem.sum() < n:
                    vals.append(roc_auc_score(mem, eleg))
            auc[q] = ("escenario", np.mean(vals))
        else:
            v = X[q] if not (o[0].get("polarity") or "").lower().startswith("inv") else 6 - X[q]
            mem = (Y[cj] == o[0]["group_label"]).astype(int).values
            auc[q] = ("Likert", roc_auc_score(mem, v))
    A = pd.DataFrame(auc, index=["formato", "auc"]).T; A.auc = A.auc.astype(float)
    for f in ("escenario", "Likert"):
        a = A[A.formato == f].auc
        print(f"  {f:9} n={len(a):2} · AUC media {a.mean():.3f} · mediana {a.median():.3f} · "
              f"ítems con AUC>.60: {int((a > .6).sum())} · con AUC<.50: {int((a < .5).sum())}")
    u = mannwhitneyu(A[A.formato == "escenario"].auc, A[A.formato == "Likert"].auc)
    print(f"  diferencia entre formatos: Mann-Whitney p={u.pvalue:.2f}")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.boxplot([A[A.formato == f].auc for f in ("escenario", "Likert")], labels=["escenario (96)", "Likert (49)"])
    ax.axhline(.5, c="k", ls="--"); ax.set_ylabel("AUC (0,5 = no distingue nada)")
    ax.set_title("X6 · ¿Qué formato reconoce mejor a los miembros de su grupo?")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "X6_formatos.png"), dpi=150); plt.close(fig)

    # X7
    print("\n== X7 · Factibilidad del 80% — ítems por conjunto necesarios para 80% por conjunto (≈ 82% por tipo)")
    def modal(p, N, R=40000):
        c = rng.multinomial(N, [p, (1 - p) / 2, (1 - p) / 2], size=R)
        top = c.max(1)
        return ((c[:, 0] == top) & ((c == top[:, None]).sum(1) == 1)).mean()
    for p in (.363, .38, .40, .42, .45, .50):
        N = next((N for N in range(6, 1201, 6) if modal(p, N) >= .80), None)
        print(f"  cada ítem acierta {p:.1%}: " + (f"{N} ítems por conjunto → {4 * N} ítems en total" if N else "más de 1200 por conjunto"))


if __name__ == "__main__":
    main()
