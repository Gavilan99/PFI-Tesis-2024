# -*- coding: utf-8 -*-
"""Análisis complementarios, segunda tanda — sin `group_label` en ningún cálculo de asociación.

    python eda_extra2.py responses_wide.csv

La asociación de un ítem (o de una opción) con una etiqueta se mide SÓLO con lo que la gente
respondió y con su etiqueta: tipo, o grupo en cada conjunto. Qué grupo «debía» elegir cada opción
según el diseño no interviene. Objetivos: los 4 conjuntos y el tipo (5 etiquetas).

  G1  asociación ítem × etiqueta (χ² por permutación, V de Cramér corregido): ¿cuánta y dónde?
  G2  lo mismo a nivel de opción (cada opción como una columna sí/no)
  G3  ¿el ranking de ítems es estable? correlación entre mitades, contra el mismo cálculo con
      etiquetas mezcladas; y qué n haría falta para que sea confiable
  G4  opciones «obviamente buenas»: elegidas por la mayoría de cualquier tipo
  G5  composición de cada grupo por tipo en esta muestra
  G6  PERMANOVA con todos, sin confianza baja, y sólo con confianza alta
  G7  diagnóstico por persona: ¿a qué perfil de tipo se parecen sus respuestas? (perfiles armados
      con las personas de confianza alta; calibrado sobre ellas mismas)
  G8  potencia: qué diferencia entre tipos se puede detectar; aquiescencia en dos versiones
  G9  escenario vs. Likert, sin group_label
  G10 matriz de confusión, F1 por tipo, conjunto compartido en cada error, atractores vs. frecuencia
  G11 meta de la v2 expresada como asociación por ítem (V de Cramér)

Salidas en eda_out/ (CSV + PNG). Semilla fija.
"""
import os, sys, collections, warnings
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import chi2 as CHI, norm

import contrast as C
from pilot_metrics import con_copias
from eda_pilot import cargar, codificar, estandarizar, permanova, chi2_bloques, bh

warnings.filterwarnings("ignore")
HERE = C.DATA   # datos y salidas, fuera del repositorio (ver README)
OUT = os.path.join(HERE, "eda_out")
AOUT = os.path.join(HERE, "analisis_out")
CONJ = list(C.GRUPOS)
rng = np.random.default_rng(0)
N_PERM = 1000


def onehot_items(X, fmt):
    oh, owners, j = [], [], 0
    for q in X.columns:
        k = 3 if fmt[q] == "scenario" else 5
        for o in range(1, k + 1):
            oh.append((X[q] == o).astype(int).values)
        owners.append(list(range(j, j + k))); j += k
    return np.column_stack(oh), owners


def onehot_opciones(X, fmt):
    """Cada opción como una variable sí/no: dos columnas (la eligió / no la eligió)."""
    oh, owners, nombres, j = [], [], [], 0
    for q in X.columns:
        k = 3 if fmt[q] == "scenario" else 5
        for o in range(1, k + 1):
            x = (X[q] == o).astype(int).values
            oh += [x, 1 - x]; owners.append([j, j + 1]); nombres.append(f"{q}_o{o}"); j += 2
    return np.column_stack(oh), owners, nombres


def etiquetas(tipos, Y):
    return {**{c: Y[c].values for c in Y.columns}, "tipo": tipos.values}


def G_of(lab):
    cl = sorted(set(lab))
    return np.column_stack([(lab == g).astype(int) for g in cl])


def v_cramer(chi, n, r, k):
    phi2 = max(0, chi / n - (k - 1) * (r - 1) / (n - 1))
    rc, kc = r - (r - 1) ** 2 / (n - 1), k - (k - 1) ** 2 / (n - 1)
    return np.sqrt(phi2 / max(1e-9, min(kc - 1, rc - 1)))


def asociacion(Oh, owners, labs, n_perm=N_PERM):
    """Para cada objetivo: χ² observado, p por permutación, y χ² nulo (matriz perm × ítem)."""
    res = {}
    for nom, lab in labs.items():
        G = G_of(lab)
        obs = chi2_bloques(Oh, owners, G)
        null = np.array([chi2_bloques(Oh, owners, G[rng.permutation(len(G))]) for _ in range(n_perm)])
        res[nom] = (obs, ((null >= obs).sum(0) + 1) / (n_perm + 1), null, G.shape[1])
    return res


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "responses_wide.csv"
    bank, X, tipos, Y, fmt = cargar(path)
    _, B, _ = con_copias()
    conf = pd.Series({c: (B[c].get("confianza") or "").strip() for c in X.index})
    items = list(X.columns); n = len(X)
    labs = etiquetas(tipos, Y)
    Oh, owners = onehot_items(X, fmt)

    # ── G1
    print("== G1 · Asociación ítem × etiqueta, sin group_label (χ², p por 1000 permutaciones)")
    A = asociacion(Oh, owners, labs)
    filas = []
    for nom, (obs, p, null, k) in A.items():
        V = np.array([v_cramer(obs[i], n, len(owners[i]), k) for i in range(len(items))])
        Vn = np.array([[v_cramer(null[b, i], n, len(owners[i]), k) for i in range(len(items))] for b in range(200)])
        q = bh(p)
        print(f"  {nom:11} ítems con p<.05: {int((p < .05).sum()):3} (azar 7,2) · q<.10: {int((q < .10).sum())} · "
              f"V medio {V.mean():.3f} (con etiquetas mezcladas {Vn.mean():.3f} ± {Vn.mean(1).std():.3f})")
        for i, it in enumerate(items):
            filas.append({"item": it, "formato": fmt[it], "objetivo": nom, "chi2": obs[i], "p": p[i],
                          "q_BH": q[i], "V": V[i]})
    G1 = pd.DataFrame(filas); G1.to_csv(os.path.join(OUT, "G1_item_x_etiqueta.csv"), index=False)
    multi = G1[G1.p < .05].groupby("item").objetivo.apply(list)
    print(f"  ítems asociados (p<.05) con 2 o más etiquetas: {sum(len(v) >= 2 for v in multi)} · "
          f"esperables por azar (5 pruebas, 5%): {len(items) * (1 - .95**5 - 5 * .05 * .95**4):.1f}")
    print("   " + ", ".join(f"{q} → {'/'.join(v)}" for q, v in multi.items() if len(v) >= 2))

    # ── G2
    print("\n== G2 · Asociación a nivel de opción (cada opción sí/no × etiqueta)")
    Oh2, ow2, nombres = onehot_opciones(X, fmt)
    A2 = asociacion(Oh2, ow2, labs, n_perm=500)
    filas = []
    for nom, (obs, p, null, k) in A2.items():
        print(f"  {nom:11} opciones con p<.05: {int((p < .05).sum()):3} de {len(nombres)} (azar {.05 * len(nombres):.1f}) · "
              f"q<.10: {int((bh(p) < .10).sum())}")
        filas += [{"opcion": nombres[i], "objetivo": nom, "p": p[i]} for i in range(len(nombres))]
    pd.DataFrame(filas).to_csv(os.path.join(OUT, "G2_opcion_x_etiqueta.csv"), index=False)

    # ── G3
    print("\n== G3 · ¿El ranking de ítems se repite en otra mitad de la gente? (200 particiones)")
    def stat_half(idx, lab):
        G = G_of(lab[idx]); ch = chi2_bloques(Oh[idx], owners, G)
        out = []
        for i, ow in enumerate(owners):
            sub = Oh[idx][:, ow]; r = int((sub.sum(0) > 0).sum())
            df_ = max(1, (r - 1) * (G.shape[1] - 1))
            out.append(-np.log10(max(CHI.sf(ch[i], df_), 1e-300)))
        return np.array(out)
    rel = {}
    for nom, lab in labs.items():
        real, nul = [], []
        for _ in range(200):
            perm = rng.permutation(n); a, b = perm[:n // 2], perm[n // 2:]
            real.append(np.corrcoef(stat_half(a, lab), stat_half(b, lab))[0, 1])
            lp = rng.permutation(lab)
            nul.append(np.corrcoef(stat_half(a, lp), stat_half(b, lp))[0, 1])
        real, nul = np.array(real), np.array(nul)
        exc = real.mean() - nul.mean()
        rel[nom] = (real.mean(), nul.mean(), exc)
        print(f"  {nom:11} etiquetas reales {real.mean():+.3f} · mezcladas {nul.mean():+.3f} · "
              f"exceso {exc:+.3f} (p≈{(nul >= real.mean()).mean():.2f})")
    print("  Proyección (Spearman-Brown sobre el exceso): confiabilidad del ranking con n personas")
    for nom, (_, _, exc) in rel.items():
        r = max(exc, 1e-3); rho_n = 2 * r / (1 + r)   # confiabilidad del ranking con las n personas de hoy
        proj = {m: (m / n * rho_n) / (1 + (m / n - 1) * rho_n) for m in (100, 200, 400, 1000)}
        need = next((m for m in range(50, 20001, 50) if (m / n * rho_n) / (1 + (m / n - 1) * rho_n) >= .7), None)
        print(f"    {nom:11} hoy (n={n}) {rho_n:.2f} · " + " · ".join(f"n={m}: {v:.2f}" for m, v in proj.items()) +
              f" · n para 0,70: {need if need else '>20000'}")

    # ── G4
    print(f"\n== G4 · Opciones elegidas por la mayoría (≥60% de las {n} personas)")
    pt = A["tipo"][1]
    rows = []
    for i, q in enumerate(items):
        k = 3 if fmt[q] == "scenario" else 5
        sh = X[q].value_counts(normalize=True)
        if sh.iloc[0] >= .60:
            top = int(sh.index[0])
            por_tipo = X.groupby(tipos)[q].apply(lambda s: (s == top).mean())
            rows.append({"item": q, "formato": fmt[q], "opcion": top, "elegida": sh.iloc[0],
                         "min_por_tipo": por_tipo.min(), "max_por_tipo": por_tipo.max(), "p_tipo": pt[i]})
    G4 = pd.DataFrame(rows).sort_values("elegida", ascending=False)
    G4.to_csv(os.path.join(OUT, "G4_opciones_mayoritarias.csv"), index=False)
    print(G4.round(2).to_string(index=False) if len(G4) else "  ninguna")

    # ── G5
    print("\n== G5 · Composición de cada grupo por tipo en esta muestra")
    cnt = tipos.value_counts()
    for conj in CONJ:
        partes = []
        for g, ts in C.GRUPOS[conj].items():
            tot = sum(cnt.get(t, 0) for t in ts)
            partes.append(f"{g} {tot} (" + " · ".join(f"{t}:{cnt.get(t, 0)}" for t in ts) + ")")
        print(f"  {C.CORTO[conj]:11} " + " | ".join(partes))

    # ── G6
    print("\n== G6 · PERMANOVA por muestra (vector completo, 1000 permutaciones)")
    import eda_pilot
    eda_pilot.N_PERM = 1000
    Z = estandarizar(codificar(X, bank, fmt))
    for nom, mask in (("todos", conf.index == conf.index), ("sin baja", conf != "baja"), ("sólo alta", conf == "alta")):
        Zm = estandarizar(codificar(X[mask], bank, fmt)).values
        celdas = []
        for obj, lab in etiquetas(tipos[mask], Y[mask]).items():
            f, r2, p = permanova(Zm, lab, rng)
            a = len(set(lab)); azar = (a - 1) / (mask.sum() - 1)
            celdas.append(f"{obj} R²={r2:.3f}/{azar:.3f} p={p:.3f}")
        print(f"  {nom:9} n={mask.sum():2}: " + " · ".join(celdas))

    # ── G7
    print("\n== G7 · ¿A qué perfil de tipo se parecen las respuestas de cada persona?")
    Zv = Z.values; idx = {c: i for i, c in enumerate(X.index)}
    alta = [c for c in X.index if conf[c] == "alta"]
    def perfil_sim(c):
        sims = {}
        for t in sorted(tipos.unique()):
            miembros = [m for m in alta if tipos[m] == t and m != c]
            if len(miembros) >= 2:
                cen = Zv[[idx[m] for m in miembros]].mean(0)
                sims[t] = np.corrcoef(Zv[idx[c]], cen)[0, 1]
        return pd.Series(sims).sort_values(ascending=False)
    rk_alta = []
    for c in alta:
        s = perfil_sim(c); rk_alta.append(list(s.index).index(tipos[c]) + 1 if tipos[c] in s.index else np.nan)
    rk_alta = np.array(rk_alta, float); ntip = len(perfil_sim(alta[0]))
    print(f"  calibración sobre los {len(alta)} de confianza alta (sin contarse a sí mismos): su propio tipo queda "
          f"1.º en {np.nanmean(rk_alta == 1):.0%} (azar {1 / ntip:.0%}) · puesto medio {np.nanmean(rk_alta):.1f} (azar {(ntip + 1) / 2:.1f})")
    filas = []
    for c in X.index[conf.isin(["baja", "media"])]:
        s = perfil_sim(c)
        puesto = list(s.index).index(tipos[c]) + 1 if tipos[c] in s.index else None
        filas.append({"codigo": c, "confianza": conf[c], "tipo_asignado": tipos[c], "puesto_de_su_tipo": puesto,
                      "1.º": f"{s.index[0]} ({s.iloc[0]:+.2f})", "2.º": f"{s.index[1]} ({s.iloc[1]:+.2f})",
                      "3.º": f"{s.index[2]} ({s.iloc[2]:+.2f})",
                      "su_tipo": f"{s.get(tipos[c], np.nan):+.2f}", "rango_similitud": f"{s.min():+.2f}…{s.max():+.2f}"})
    G7 = pd.DataFrame(filas); G7.to_csv(os.path.join(OUT, "G7_perfil_por_persona.csv"), index=False)
    print(G7.to_string(index=False))

    # ── G8
    print("\n== G8 · Potencia y aquiescencia")
    za, zb = norm.ppf(.975), norm.ppf(.80)
    for nt in (3, 5, 6, 8, 10, 20, 30):
        d = (za + zb) * np.sqrt(1 / nt + 1 / (n - nt))
        print(f"  un tipo con {nt:2} personas contra el resto: diferencia mínima detectable d = {d:.2f} desvíos")
    lik = [q for q in items if fmt[q] == "likert"]
    acq_media = X[lik].mean(axis=1)
    acq_ord = X[lik].isin([4, 5]).mean(axis=1) - X[lik].isin([1, 2]).mean(axis=1)
    est = pd.DataFrame({"aquiescencia_media": acq_media, "aquiescencia_ordinal": acq_ord,
                        "punto_medio": (X[lik] == 3).mean(axis=1), "extremos": X[lik].isin([1, 5]).mean(axis=1),
                        "concentracion": X[lik].apply(lambda r: r.value_counts().iloc[0] / len(r), axis=1)})
    print(f"  aquiescencia (media 1–5) vs. aquiescencia ordinal (%acuerdo − %desacuerdo): Spearman "
          f"{acq_media.corr(acq_ord, method='spearman'):+.2f}")
    for c in est:
        sd = est[c].std()
        print(f"  {c:21} mediana {est[c].median():+.2f} · desvío {sd:.3f} → con n=6 por tipo se detecta una diferencia de "
              f"~{(za + zb) * np.sqrt(1 / 6 + 1 / (n - 6)) * sd:.3f}; con n=20, ~{(za + zb) * np.sqrt(1 / 20 + 1 / (n - 20)) * sd:.3f}")
    est["tipo"] = tipos; est.to_csv(os.path.join(OUT, "G8_estilo.csv"))
    print("  medianas por tipo:")
    print(est.groupby("tipo").median().round(2).to_string().replace("\n", "\n    "))

    # ── G9
    print("\n== G9 · Escenario vs. Likert sin group_label: fracción de ítems asociados (p<.05) por etiqueta")
    for f in ("scenario", "likert"):
        s = G1[G1.formato == f]
        print(f"  {f:9} " + " · ".join(f"{o} {(s[s.objetivo == o].p < .05).mean():.0%}" for o in labs) +
              f" · V medio {s.V.mean():.3f}   (azar: 5% en cada uno)")

    # ── G10
    print("\n== G10 · Matriz de confusión de la intersección (20 repeticiones sumadas), F1, conjunto compartido")
    cm = pd.read_csv(os.path.join(AOUT, "E_matriz_confusion.csv"), index_col=0)
    cm.index = cm.index.astype(int); cm.columns = cm.columns.astype(int)
    print("  filas = tipo real · columnas = tipo predicho")
    print(cm.to_string().replace("\n", "\n    "))
    filas = []
    for t in cm.index:
        tp = cm.at[t, t]; real = cm.loc[t].sum(); pred = cm[t].sum()
        if real == 0:
            continue
        prec = tp / pred if pred else 0; rec = tp / real
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
        filas.append({"tipo": t, "n_muestra": int(cnt.get(t, 0)), "real": int(real), "predicho": int(pred),
                      "predicho/real": pred / real, "precision": prec, "recall": rec, "F1": f1})
    F = pd.DataFrame(filas); F.to_csv(os.path.join(OUT, "G10_f1_por_tipo.csv"), index=False)
    print(F.round(2).to_string(index=False))
    print(f"  F1 macro {F.F1.mean():.2f} · referencia azar (predecir al azar con la prevalencia de la muestra: "
          f"F1 de cada tipo = su prevalencia) ≈ {(cnt / n).mean():.2f}")
    print(f"  ¿los tipos más frecuentes se predicen de más? Spearman(n en la muestra, predicho/real) = "
          f"{F.n_muestra.corr(F['predicho/real'], method='spearman'):+.2f}")
    sh = pd.DataFrame(0, index=cm.index, columns=[C.CORTO[c] for c in CONJ])
    for t in cm.index:
        for p in cm.columns:
            if t != p and cm.at[t, p]:
                for c in CONJ:
                    if C.grupo_de(t, c) == C.grupo_de(p, c):
                        sh.at[t, C.CORTO[c]] += cm.at[t, p]
    sh = sh[sh.sum(axis=1) > 0]
    print("  errores por tipo real, según el conjunto que comparten real y predicho (= el único que acertó):")
    print(sh.to_string().replace("\n", "\n    "))
    print("  totales: " + " · ".join(f"{c} {sh[c].sum()} ({sh[c].sum() / sh.values.sum():.0%})" for c in sh.columns))
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    rows = cm.loc[[t for t in cm.index if cm.loc[t].sum()]]
    im = ax.imshow((rows.T / rows.sum(axis=1)).T, cmap="Blues", vmin=0, vmax=.5)
    for i, t in enumerate(rows.index):
        for j, p in enumerate(rows.columns):
            v = rows.at[t, p]
            if v:
                ax.text(j, i, int(v), ha="center", va="center", fontsize=7)
    ax.set_xticks(range(len(rows.columns))); ax.set_xticklabels(rows.columns); ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows.index); ax.set_xlabel("tipo predicho"); ax.set_ylabel("tipo real")
    ax.set_title("Matriz de confusión (intersección, 20 repeticiones)\ncolor = fracción de la fila · número = conteo")
    fig.colorbar(im, ax=ax, shrink=.8); fig.tight_layout()
    fig.savefig(os.path.join(OUT, "G10_matriz_confusion.png"), dpi=150); plt.close(fig)

    # ── G11
    print("\n== G11 · Meta de la v2 en términos de asociación por ítem (V de Cramér con su conjunto)")
    for p in (.363, .40, .45, .50):
        t = np.full((3, 3), (1 - p) / 2 / 3); np.fill_diagonal(t, p / 3)
        phi2 = ((t - 1 / 9) ** 2 / (1 / 9)).sum()
        print(f"  un escenario que acierta el grupo {p:.1%} de las veces ≈ V {np.sqrt(phi2 / 2):.3f}")
    s = G1[(G1.formato == "scenario") & (G1.objetivo != "tipo")]
    print(f"  hoy, V medio de los escenarios contra los 4 conjuntos: {s.V.mean():.3f} · p90 {s.V.quantile(.9):.3f}")


if __name__ == "__main__":
    main()
