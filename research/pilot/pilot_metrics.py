# -*- coding: utf-8 -*-
"""Métricas de corte del piloto — una sola fuente para todas las cifras de las notas de contraste.

    python pilot_metrics.py responses_wide.csv [--previo N]

`--previo N` marca como nuevos a los respondentes posteriores a la posición N del export
(el export conserva el orden de envío), para poder decir qué aportó cada tanda.

POR QUÉ EXISTE
--------------
Hasta n=35 las métricas de las notas `Piloto · … contraste` se calcularon con scripts ad hoc
que no se guardaron. Al reconstruirlas en n=44, la intersección del corte n=35 dio 6/34 y no
los 8/34 reportados: la diferencia estaba en cómo se trataban los empates del modal, y sin el
script no había forma de saberlo. **Toda cifra de una nota de corte sale de acá.** Si se
cambia una definición, se cambia acá y se anota en la nota del corte siguiente.

DEFINICIONES (fijas)
--------------------
· Exclusiones: los códigos de `excluidos.txt` en la carpeta de datos (ver `contrast.EXCLUIDOS`).
· **Acierto por conjunto** — grupo modal de los 24 escenarios del conjunto. ESTRICTO: un
  empate en el primer lugar no cuenta como acierto aunque incluya el grupo esperado.
· **Línea de base** — «contestar siempre el grupo más común de la muestra».
· **Discriminación de grupo** — % de elecciones al grupo entre miembros menos el % entre no
  miembros. El ideal no es 33%: es miembros alto y no miembros cerca de 0.
· **Intersección** — modal de escenario por conjunto; un empate aporta la UNIÓN de los tipos
  de los grupos empatados. Si los cuatro intersectan en un tipo → 4/4. Si no, regla de los
  tríos: si exactamente un trío cierra en un tipo, ése es el resultado; si cierran varios, no
  hay resultado único y cuenta como fallo.
· **H1** — share de Apego en los escenarios de Relaciones entre quienes NO son 3/6/9; test de
  signos contra 1/3.
· **Estilo del 6** — concentración de ancla Likert (share del ancla más usada), tipo 6 contra
  el resto; U de Mann-Whitney por permutación (200 000, semilla fija). Umbral registrado para
  el test limpio: n(6) ≥ 10.
· **Familiaridad** — naive = Nada + Algo; experto = Bastante + Mucho. Se reporta el test POR
  PERSONA. El test por celdas trata 8 celdas de una persona como independientes y da un p
  optimista; se imprime sólo como referencia.
"""
import csv, io, os, sys, math, random, shutil, subprocess, tempfile, collections
import contrast as C

EXC = C.EXCLUIDOS
REPS = 200_000


def con_copias():
    """A veces Python no puede abrir las planillas (Excel u OneDrive las retienen), aunque el
    sistema sí puede copiarlas. Si pasa, se leen copias temporales — nunca se escribe sobre los
    originales."""
    try:
        return C.cargar_banco(), C.cargar_b(), C.cargar_prior()
    except PermissionError:
        tmp = tempfile.mkdtemp()
        for f in ("Piloto B - Tipificaciones.xlsx", "Piloto C - Prior (sellado).xlsx",
                  "NureonAI Prototype v4.1.csv"):
            src = os.path.join(C.PROJ, f)
            if not os.path.exists(src):
                continue
            try:
                shutil.copy(src, tmp)
            except PermissionError:   # copia del sistema, que no choca con el bloqueo
                subprocess.run(["powershell", "-NoProfile", "-Command",
                                f"Copy-Item -LiteralPath '{src}' -Destination '{tmp}'"], check=True)
        C.PROJ = tmp
        print("(planillas bloqueadas para Python — leídas desde copias temporales)\n")
        return C.cargar_banco(), C.cargar_b(), C.cargar_prior()


def binom_sf(k, n, p):
    return sum(math.comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k, n + 1))


def fisher_1(a, b, c, d):
    """Una cola: la primera fila tiene más aciertos."""
    n1, n2, k = a + b, c + d, a + c
    return sum(math.comb(n1, x) * math.comb(n2, k - x)
               for x in range(a, min(n1, k) + 1)) / math.comb(n1 + n2, k)


def perm_u(a, b, seed):
    """U de Mann-Whitney de `a` sobre `b`, p de una cola por permutación."""
    U = lambda x, y: sum((i > j) + .5 * (i == j) for i in x for j in y)
    u0, v, k = U(a, b), list(a) + list(b), 0
    rnd = random.Random(seed)
    for _ in range(REPS):
        rnd.shuffle(v)
        k += U(v[:len(a)], v[len(a):]) >= u0
    return k / REPS


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); return 2
    previo = None
    if "--previo" in sys.argv:
        previo = int(sys.argv[sys.argv.index("--previo") + 1])
        args = [a for a in args if a != str(previo)]

    bank, B, _ = con_copias()
    R = {r["respondent_id"]: r for r in csv.DictReader(io.open(args[0], encoding="utf-8"))}
    orden = list(R)
    nuevos = orden[previo:] if previo is not None else []
    use = [c for c in orden if c not in EXC and B.get(c) and B[c].get("tipo_asignado")]
    T = {c: int(B[c]["tipo_asignado"]) for c in use}
    sin_tipo = [c for c in orden if c not in T and c not in EXC]

    esc = lambda c, conj: C.perfil(R[c], bank, conj, "scenario")[0]
    def modal(d):
        m = max(d.values()); return [g for g in d if d[g] == m]

    print(f"n usable (sin {sorted(EXC)}): {len(use)}" + (f" · sin tipo en B: {sin_tipo}" if sin_tipo else ""))
    print("tipos:", " · ".join(f"{t}×{n}" for t, n in sorted(collections.Counter(T.values()).items())))
    if nuevos:
        print("nuevos:", ", ".join(f"{c} (t{T.get(c)}, {B.get(c, {}).get('origen_tipo')}, "
                                   f"conf {B.get(c, {}).get('confianza')})" for c in nuevos))
    sin_origen = [c for c in use if not B[c].get("origen_tipo")]
    if sin_origen:
        print("sin origen_tipo:", sin_origen)

    # 1 · acierto por conjunto
    print("\n== 1 · Acierto por conjunto (modal de escenarios, estricto) contra la línea de base")
    ta = tb = 0
    for conj in C.GRUPOS:
        exp = collections.Counter(C.grupo_de(T[c], conj) for c in use)
        hit = sum(modal(esc(c, conj)) == [C.grupo_de(T[c], conj)] for c in use)
        g0, base = exp.most_common(1)[0]
        ta += hit; tb += base
        print(f"  {C.CORTO[conj]:11} {hit}/{len(use)} = {hit/len(use):.0%}   base {base/len(use):.0%} ({g0})")
    N = 4 * len(use)
    print(f"  TOTAL       {ta}/{N} = {ta/N:.1%}   base {tb/N:.1%}   P(X≥{ta} | 1/3) = {binom_sf(ta, N, 1/3):.3f}")
    if nuevos:
        nu = [c for c in nuevos if c in T]
        h = sum(modal(esc(c, conj)) == [C.grupo_de(T[c], conj)] for c in nu for conj in C.GRUPOS)
        print(f"  sólo nuevos: {h}/{4*len(nu)}" + (f" = {h/4/len(nu):.0%}" if nu else ""))
    lk = sum(modal(C.perfil(R[c], bank, conj, "likert")[0]) == [C.grupo_de(T[c], conj)]
             for c in use for conj in C.GRUPOS)
    print(f"  Likert (estricto): {lk}/{N} = {lk/N:.1%}")

    # 2 · acierto del grupo propio
    print("\n== 2 · Acierto modal cuando el grupo es el propio")
    for conj in C.GRUPOS:
        for g, ts in C.GRUPOS[conj].items():
            mem = [c for c in use if T[c] in ts]
            h = sum(modal(esc(c, conj)) == [g] for c in mem)
            print(f"  {g:12} {h}/{len(mem)}" + (f" ({h/len(mem):.0%})" if mem else ""))

    # 3 · discriminación
    print("\n== 3 · Discriminación: % al grupo entre miembros − no miembros")
    filas = []
    for conj in C.GRUPOS:
        for g, ts in C.GRUPOS[conj].items():
            def share(cs):
                return (sum(esc(c, conj)[g] for c in cs) /
                        sum(sum(esc(c, conj).values()) for c in cs)) if cs else float("nan")
            mem = [c for c in use if T[c] in ts]; non = [c for c in use if T[c] not in ts]
            filas.append((share(mem) - share(non), g, share(mem), len(mem), share(non), len(non)))
    for idx, g, sm, nm, sn, nn in sorted(filas, reverse=True):
        print(f"  {g:12} miembros {sm:.0%} (n={nm:2})  no {sn:.0%} (n={nn:2})  {idx:+.0%}")

    # 4 · intersección
    print("\n== 4 · Intersección (modal de escenarios + regla de los tríos)")
    def resolver(tops):
        sets = {k: set().union(*[set(C.GRUPOS[k][g]) for g in v]) for k, v in tops.items()}
        full = set.intersection(*sets.values())
        if full:
            return full, "4/4" if len(full) == 1 else "ambiguo"
        tr = []
        for drop in sets:
            s = set.intersection(*[v for k, v in sets.items() if k != drop])
            if len(s) == 1:
                tr.append((next(iter(s)), drop))
        if len(tr) == 1:
            return {tr[0][0]}, f"trío sin {C.CORTO[tr[0][1]]}"
        return {t for t, _ in tr}, f"{len(tr)} tríos"
    res = {c: resolver({k: modal(esc(c, k)) for k in C.GRUPOS}) for c in use}
    ok = {c: res[c][0] == {T[c]} for c in use}
    hits = sum(ok.values())
    real = collections.Counter(T.values())
    base_t = max(real.values())
    print(f"  acierta {hits}/{len(use)} = {hits/len(use):.0%} · base «tipo más común» "
          f"{base_t/len(use):.0%} · azar 11% · P(X≥{hits} | 1/9) = {binom_sf(hits, len(use), 1/9):.3f}")
    print("  formas:", dict(collections.Counter(k.split(" sin")[0] for _, k in res.values())))
    if previo is not None:
        viejos = [c for c in use if c not in nuevos]
        print(f"  mismo método sobre el corte previo: {sum(ok[c] for c in viejos)}/{len(viejos)}")
    pred = collections.Counter(next(iter(s)) for s, _ in res.values() if len(s) == 1)
    print("  tipo · real · predicho · acierto")
    for t in range(1, 10):
        print(f"    {t}   {real[t]:3}  {pred[t]:5}     {sum(ok[c] for c in use if T[c] == t)}/{real[t]}")
    print(f"  fuga a Competente (1·3·5): predichos {sum(pred[t] for t in (1,3,5))}, "
          f"reales {sum(real[t] for t in (1,3,5))}")
    for c in nuevos:
        if c in res:
            print(f"    {c} t{T[c]} → {sorted(res[c][0])} ({res[c][1]})")

    # 5 · H1
    print("\n== 5 · H1 — Apego entre quienes no son 3/6/9")
    rel = "Conjunto de Relaciones Objetales"
    xs = [esc(c, rel)["Apego"] / sum(esc(c, rel).values()) for c in use if T[c] not in (3, 6, 9)]
    up = sum(x > 1/3 for x in xs)
    print(f"  media {sum(xs)/len(xs):.0%} · {up}/{len(xs)} sobre el azar · signos p = {binom_sf(up, len(xs), .5):.3f}")

    # 6 · estilo del 6
    print("\n== 6 · Estilo — concentración de ancla Likert, tipo 6 contra el resto")
    def conc(c):
        v = [R[c][q] for q, o in bank.items() if o[0]["format"] == "likert"
             and R[c].get(q) not in (None, "", C.NOT_ASKED)]
        return max(collections.Counter(v).values()) / len(v)
    six = [conc(c) for c in use if T[c] == 6]; rest = [conc(c) for c in use if T[c] != 6]
    print(f"  n(6) = {len(six)} (umbral del test limpio: 10) · 6: {sorted(round(100*x) for x in six)}")
    print(f"  permutación, una cola: p = {perm_u(six, rest, 1):.4f}")
    print("  extremos:", ", ".join(f"{c} t{T[c]} {conc(c):.0%}"
                                  for c in sorted(use, key=conc, reverse=True)[:6]))

    # 7 · ítem por ítem
    print("\n== 7 · Ítem por ítem (escenarios): fracción que elige su propio grupo")
    fr = []
    for q, o in bank.items():
        if o[0]["format"] != "scenario":
            continue
        v = [o[int(R[c][q]) - 1]["group_label"] == C.grupo_de(T[c], o[0]["grouping_system"])
             for c in use if R[c].get(q) not in (None, "", C.NOT_ASKED)]
        fr.append((sum(v) / len(v), q, len(v)))
    m = sum(f for f, *_ in fr) / len(fr)
    sd = (sum((f - m)**2 for f, *_ in fr) / (len(fr) - 1))**.5
    sd0 = (2 / 9 / len(use))**.5
    crit = next(k for k in range(len(use) + 1) if binom_sf(k, len(use), 1/3) < .05)
    print(f"  media {m:.1%} · desvío {sd:.1%} · por ruido {sd0:.1%} · razón {sd/sd0:.2f}× · "
          f"p<.05: {sum(f*n >= crit for f, _, n in fr)}/{len(fr)} "
          f"(esperados {len(fr)*binom_sf(crit, len(use), 1/3):.1f})")

    # 8 · familiaridad
    print("\n== 8 · Familiaridad (escenario + Likert, estricto)")
    exp_ = lambda c: R[c].get("meta_familiaridad", "").strip() in ("Bastante", "Mucho, lo estudié")
    pp = {c: (lambda e: sum(x[2] for x in e) / len(e))(C.evaluar(R[c], bank, T[c])) for c in use}
    ex = [c for c in use if exp_(c)]; nv = [c for c in use if not exp_(c)]
    for k, cs in (("naive", nv), ("experto", ex)):
        print(f"  {k:8} n={len(cs):2}  media {sum(pp[c] for c in cs)/len(cs):.0%}")
    print(f"  por persona (permutación): p = {perm_u([pp[c] for c in ex], [pp[c] for c in nv], 2):.3f}")
    a = round(sum(pp[c] for c in ex) * 8); b = round(sum(pp[c] for c in nv) * 8)
    print(f"  por celdas (optimista, sólo referencia): Fisher p = {fisher_1(a, 8*len(ex)-a, b, 8*len(nv)-b):.3f}")
    print("  expertos:", ", ".join(f"{c} ({B[c].get('origen_tipo')}) {pp[c]:.0%}" for c in ex))

    # 9 · origen
    print("\n== 9 · Por origen de la etiqueta (escenarios, estricto)")
    o = collections.defaultdict(lambda: [0, 0])
    for c in use:
        k = (B[c].get("origen_tipo") or "sin declarar").strip()
        for conj in C.GRUPOS:
            o[k][0] += modal(esc(c, conj)) == [C.grupo_de(T[c], conj)]; o[k][1] += 1
    for k, (a, t) in sorted(o.items()):
        print(f"  {k:22} n={t//4:2}  {a}/{t} = {a/t:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
