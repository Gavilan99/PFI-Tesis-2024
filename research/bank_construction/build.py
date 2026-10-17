# -*- coding: utf-8 -*-
"""Builds the NureonAI question bank: validates, then emits CSV + markdown."""
import csv, sys, collections, random, re, unicodedata, itertools, json, io, os
import accents

# --prototype builds a small prototype set instead of the 200-item bank, using
# THE SAME code path. Three checks are size-dependent and are relaxed below with
# a printed reason; everything else runs identically.
PROTOTYPE = "--prototype" in sys.argv

if PROTOTYPE:
    import p41_centros as centros, p41_horneviano as horneviano
    import p41_armonico as armonico, p41_relaciones as relaciones
    BUILD_NAME = "NureonAI Prototype v4.1"
    EXPECT_PER_SYSTEM = None   # bank expects 50/system; a prototype has no target
    MIN_PAIRS = 0              # the >=500 objective is a bank property, not a prototype one
    # 2026-09-18: reactivado. El motivo original ("~6 ítems por conjunto") caducó:
    # el prototipo cerró en 24 de escenario por conjunto, que ya admite el chequeo.
    CHECK_POSITION = True
else:
    import centros, horneviano, armonico, relaciones
    BUILD_NAME = "NureonAI Question Bank v1.2"
    EXPECT_PER_SYSTEM = 50
    MIN_PAIRS = 500
    CHECK_POSITION = True

# Option length bounds, in words. Likert has a higher floor: a scenario option
# inherits context from its stem ("Que fuiste una carga" works at 4 words because
# the stem carries it), while a Likert statement carries its own context.
# See rule 8 of [[Ítems Likert — Reglas de Redacción]].
MIN_WORDS, MAX_WORDS = 4, 20
# 2026-09-14 — [[Ítems Likert — Enmienda 1]]: el techo de longitud Likert se
# eliminó. Un anclaje-ocasión cuesta palabras, y contra un techo sólo se puede
# comprar espacio dejando la escena implícita o acortando los verbos: las dos
# cosas que hundieron la primera redacción de Horneviano. Las restricciones
# vinculantes pasan a ser una sola proposición y la comprensión en una lectura,
# que no son mecanizables. El piso se mantiene. LIKERT_REPORT_WORDS sólo informa.
LIKERT_MIN_WORDS, LIKERT_MAX_WORDS = 8, None
LIKERT_REPORT_WORDS = 24

# ---- lexical saturation / opening monotony (added after batch 1) ----
# Batch 1's two real defects were invisible to every check that existed:
#   - "cuerpo" in 5 of 12 Cuerpo options in one author's set;
#   - "Sentir" opening 15 of 36 options in the other's.
# Both are the failure the memos warn about — a recommended word becoming the
# group's lexicalised proxy — and both were only caught by ad-hoc scripts.
# Thresholds are proportional so they hold at 12 options and at 40.
SATURATION_SHARE = 0.25   # a content word in >=25% of a group's options
SATURATION_MIN = 3        # ...and at least this many, so tiny sets don't fire
OPENING_SHARE = 0.25      # a single first word opening >=25% of a conjunto's options

# Concessive connectors ("X, aunque Y") are the natural way to write the cost that
# rule 1b of the Likert memo demands, so they appear for a good reason — but in the
# first Likert batch one author used "aunque" in 7 of 12 statements and the merged
# set still carried 5 of 12, with one statement using it twice. Same shape as the
# "Sentir que..." template in the scenario batch, and it showed up in BOTH authors:
# it is a property of the format, not of a writer.
CONCESSIVE = r"\b(aunque|a pesar de|si bien|pese a|aun asi|igual que si)\b"
CONCESSIVE_SHARE = 0.33   # flag when a third or more of a conjunto's items use one

ITEM_TEMPLATE_N = 2       # options out of 3, in ONE item, sharing an opening
ITEM_TEMPLATE_WORDS = 3   # how many leading words count as "the same opening"

# Stem checks (2026-09-10). Both warn-only; both need a human to read the domain.
# A stem whose situation is a bare indefinite — "armando algo", "un asunto ajeno" — makes each
# respondent invent a different scene. Naming the object is the only fix.
VAGUE_OBJECT = (r"(\b(armando|organizando|haciendo|preparando|encarando|resolviendo)\s+"
                r"(algo|una cosa)\b|\basunto\s+ajeno\b|\balgo\s+ajeno\b|"
                r"\bcuanto\s+poner\b|\bun\s+tema\s+(ajeno|de\s+otro)\b)")
# "Pesar"/"costar"/"molestar" frame the stem as burden. Correct when the domain is already
# negative, wrong when it is neutral or positive — so the flag fires only without a marker.
NEGATIVE_STEM_VERB = r"\b(pesa|te pesa|cuesta|te cuesta|molesta|tolerarias|soportarias)\b"
NEGATIVE_DOMAIN = (r"\b(no |sin |nada |nadie |problema|conflicto|error|falla|mal |dificil|"
                   r"perder|perdes|encima|dificultad|discusion|pelea|menos|cuesta|te cuesta|"
                   r"varias cosas|al mismo tiempo|bloquea|frena|incomod\w+|"
                   # 2026-09-12: falsos positivos de Armónico — el conjunto entero es negativo
                   # pero muchos dominios lo dicen con verbos que el patrón no tenía.
                   r"echaron|despid\w+|arruin\w+|rompe|rompio|atras\w+|deuda|cuota|"
                   r"se cae|cancel\w+|tormenta|olvid\w+|malentien\w+|falta |perjudic\w+|"
                   r"no alcanza|mas alta de lo|se pelean|tenso|no levanta)")

# Function words carry no construct meaning; counting them would drown the signal.
STOP = set("""que de la el los las un una y o a en se te lo le su tu vos no es mas más por
para con del al sin ya si como cuando mi me nos ese esa eso este esta esto muy tan ser estar
hacer tener todo toda todos algo cada dos ni son era hay solo sola bien mal cosa cosas""".split())

# Share of Likert items per conjunto that should be semantically inverse.
# Rule 7 of the Likert memo: 20-30%, NOT 50% — reverse-worded items generate
# method factors, documented especially in Spanish-language instruments.
INVERSE_MIN, INVERSE_MAX = 0.20, 0.30

# Fixed seed: option order is randomised but reproducible.
# Rationale: with a fixed order, option position was perfectly confounded with
# group_label (pos 1 always Cuerpo, pos 2 always Corazon, ...), so any position
# bias would be indistinguishable from the construct. Scoring key travels with
# the option, not the position.
RNG = random.Random(20260817)

# ---------------------------------------------------------------------------
# 2026-09-18 — ORDEN DE OPCIONES BALANCEADO POR CONSTRUCCIÓN.
# Hasta hoy el orden salía de RNG.shuffle() por ítem: aleatorio y reproducible,
# pero sin garantía de balance. Al reactivar el chequeo de posición sobre los 24
# ítems por conjunto, chi-cuadrado rechazó la independencia en dos conjuntos
# (Centros p=0.0003, con Corazón primero en 16 de 24; Armónico p=0.045). Y
# make_form.gs NO baraja, confiando explícitamente en ese de-confounding, así que
# el sesgo llegaba intacto al respondente.
# Con tres grupos hay seis permutaciones; repartidas en partes iguales, cada
# grupo cae exactamente n/3 veces en cada posición y chi-cuadrado es 0 por
# diseño, no por suerte de semilla. El orden ENTRE ítems sigue barajado con la
# misma semilla, así que el formulario sigue siendo reproducible.
def _balanced_perms(n_items, n_groups=3):
    perms = list(itertools.permutations(range(n_groups)))
    reps = -(-n_items // len(perms))
    pool = (perms * reps)[:n_items]
    RNG.shuffle(pool)
    return pool

_PERMS, _PERM_I = {}, collections.Counter()

LIKERT = [("Muy en desacuerdo", 1), ("En desacuerdo", 2), ("Neutral", 3),
          ("De acuerdo", 4), ("Muy de acuerdo", 5)]

MODULES = [centros, horneviano, armonico, relaciones]

# 2026-09-19 — PALABRAS-CONSTRUCTO. El chequeo de saturación existe para que el
# clasificador no aprenda una palabra en vez del constructo. Pero en algunos
# grupos la palabra ES el constructo: en Corazón *sentir*, en Frustración
# *mejor*. Avisar de eso mezclado con saturaciones reales enseña a ignorar el
# aviso. Estas se informan aparte; cualquier otra sigue siendo advertencia.
# La lista es corta y declarada a propósito: no es una salida para silenciar
# avisos incómodos, es el vocabulario que el memo del conjunto define como
# mecanismo. Nótese que *sentís* en Complaciente y *poder* en Retraída NO están:
# son verbos genéricos, no constructo, y siguen dando advertencia.
CONSTRUCT_WORDS = {
    ("Centros de Inteligencia", "Cuerpo"):       {"cuerpo", "tension"},
    ("Centros de Inteligencia", "Corazón"):      {"sentir"},
    ("Centros de Inteligencia", "Mente"):        {"orientarte", "orientar"},
    ("Conjunto de Relaciones Objetales", "Frustración"): {"mejor"},
}

# Minimum share of an conjunto's scenario items in which a given type must be
# reachable — i.e. have at least one option written to reach it. See rule 9 of
# the v2 design rules. A fully group-level item reaches every type exactly once
# (via its own group's option), so an all-group-level bank scores 100% here.
# Flavouring an option strands the other two members of that group in that item;
# this floor is what forces the compensation to actually happen elsewhere.
REACH_FLOOR = 0.80


def parse_option(opt, mod):
    """Options are (text, group) or (text, group, [types]).

    `type_coverage` is the SET of member types the option is written to reach.
    Omitted means fully group-level: all three members. Documentation only —
    never read at prediction time, exactly like group_label.
    """
    if len(opt) == 2:
        text, grp = opt
        cov = list(mod.GROUP_TYPES[grp])
    else:
        text, grp, cov = opt
        cov = list(cov)
    return text, grp, cov


rows = []          # flat question+option pairs
questions = []     # question-level records
qid = 0
cov_errs = []

for mod in MODULES:
    for origin, src, prompt, qtype, opts in mod.ITEMS:
        qid += 1
        code = "Q%03d" % qid
        polarity = "n/a"
        if qtype == "likert":
            # opts is either a bare group string (polarity defaults to "directa")
            # or a (group, polarity) tuple. Polarity is DOCUMENTATION ONLY — the
            # Random Forest sees the raw ordinal position and learns for itself
            # that low values predict the group on an inverse item. Nothing is
            # flipped at prediction time. See rule 9 of the Likert memo.
            if isinstance(opts, (tuple, list)):
                target, polarity = opts
            else:
                target, polarity = opts, "directa"
            if polarity not in ("directa", "inversa"):
                cov_errs.append(f"{code}: polarity {polarity!r} must be directa|inversa")
            # Likert keeps its natural ordered scale — never shuffled.
            options = [(label, target, list(mod.GROUP_TYPES[target]), order)
                       for label, order in LIKERT]
        else:
            parsed = [parse_option(o, mod) for o in opts]
            if mod.SYSTEM not in _PERMS:
                _n = sum(1 for it in mod.ITEMS
                         if (it[3] if len(it) > 3 else "scenario") == "scenario")
                _PERMS[mod.SYSTEM] = _balanced_perms(_n, len(mod.GROUPS))
            # orden canónico por grupo, después la permutación asignada
            _canon = sorted(parsed, key=lambda x: mod.GROUPS.index(x[1]))
            _perm = _PERMS[mod.SYSTEM][_PERM_I[mod.SYSTEM] % len(_PERMS[mod.SYSTEM])]
            _PERM_I[mod.SYSTEM] += 1
            parsed = [_canon[k] for k in _perm]
            options = [(t, g, c, i + 1) for i, (t, g, c) in enumerate(parsed)]
        for text, grp, cov, _ in options:
            legal = set(mod.GROUP_TYPES.get(grp, ()))
            if not cov:
                cov_errs.append(f"{code}: empty type_coverage on {text[:34]!r}")
            elif not set(cov) <= legal:
                cov_errs.append(
                    f"{code}: type_coverage {sorted(set(cov) - legal)} not members "
                    f"of {grp} on {text[:34]!r}")
        questions.append(dict(id=code, system=mod.SYSTEM, origin=origin, source=src,
                              prompt=prompt, qtype=qtype, n_opts=len(options),
                              polarity=polarity,
                              groups=[g for _, g, _, _ in options],
                              coverage=[c for _, _, c, _ in options]))
        for text, grp, cov, order in options:
            rows.append(dict(question_id=code, grouping_system=mod.SYSTEM,
                             question_type=("multiple_choice" if qtype == "likert" else "scenario"),
                             format=qtype, prompt=prompt, option_text=text,
                             group_label=grp,
                             type_coverage="|".join(str(t) for t in sorted(cov)),
                             polarity=polarity,
                             display_order=order, origin=origin))

# ---------------- validation ----------------
errs, warns = [], []

print("=" * 62)
print(f"VALIDATION — {BUILD_NAME}" + ("  [PROTOTYPE MODE]" if PROTOTYPE else ""))
print("=" * 62)

if PROTOTYPE:
    print("\nRelaxed for prototype mode, with reasons:")
    print("  - questions-per-system target: skipped (50/system is a bank target,")
    print("    a prototype has no such target)")
    print("  - >=500 question+answer pairs: skipped (that is the §1.2 objective")
    print("    for the bank, meaningless for a 24-item set)")
    print("  - position x group_label: skipped (with ~6 items per conjunto a given")
    print("    group misses a given slot by chance alone with probability (2/3)^6")
    print("    ~= 8.8%; across 36 cells ~3 empty cells are expected with a perfectly")
    print("    good shuffle, so the check reports noise, not defects)")

by_sys = collections.Counter(q["system"] for q in questions)
print("\nQuestions per grouping system:")
for s, n in by_sys.items():
    print(f"  {s:38} {n:3}")
    if EXPECT_PER_SYSTEM is not None and n != EXPECT_PER_SYSTEM:
        warns.append(f"{s} has {n} questions, expected {EXPECT_PER_SYSTEM}")

print(f"\nTOTAL QUESTIONS: {len(questions)}")
print(f"TOTAL QUESTION+ANSWER PAIRS: {len(rows)}")
if len(rows) < MIN_PAIRS:
    errs.append(f"Only {len(rows)} pairs — below the {MIN_PAIRS} objective")

print("\nOrigin split:")
for o, n in collections.Counter(q["origin"] for q in questions).items():
    print(f"  {'reworked from Anexo C' if o=='R' else 'net-new':38} {n:3}")

print("\nFormat split:")
for f, n in collections.Counter(q["qtype"] for q in questions).items():
    print(f"  {f:38} {n:3}")

# group_label balance within each system (scenario items only — likert is 1 group x5)
print("\nScenario-item balance per group_label:")
for mod in MODULES:
    c = collections.Counter()
    for q in questions:
        if q["system"] == mod.SYSTEM and q["qtype"] == "scenario":
            for g in q["groups"]:
                c[g] += 1
    print(f"  {mod.SYSTEM}")
    for g in mod.GROUPS:
        print(f"    {g:22} {c[g]:3}")
    if len(set(c.values())) > 1:
        warns.append(f"{mod.SYSTEM}: scenario group_labels unbalanced -> {dict(c)}")

# 2026-09-17 — PAR DE CONTROL. El ítem 44 de Relaciones existe en las dos
# polaridades sobre el mismo anclaje y la misma faceta: es el experimento que
# decide si la version endurecida de la regla 7b (el set que acuerda no puede
# contener entero a ningun grupo) es correcta. Cuenta como UN item de diseño a
# efectos del balance por grupo, aunque se administren los dos. Cualquier otro
# par con la misma raiz de nota tambien contaria una vez: la exencion es de
# pares declarados, no una relajacion del chequeo.
def _design_key(q):
    src = (q.get("source") or "")
    m = re.match(r"^(rlik 44)[di]\b", src)
    return m.group(1) if m else q["id"]

print("\nLikert balance per group_label (must be equal within a conjunto):")
for mod in MODULES:
    lk = [q for q in questions if q["system"] == mod.SYSTEM and q["qtype"] == "likert"]
    _seen, _uniq = set(), []
    for q in lk:
        k = _design_key(q)
        if k in _seen:
            continue
        _seen.add(k); _uniq.append(q)
    if len(_uniq) != len(lk):
        print(f"    (par de control: {len(lk) - len(_uniq)} item(s) cuentan una vez "
              f"para el balance; se administran los dos)")
    lk = _uniq
    c = collections.Counter(q["groups"][0] for q in lk)
    print(f"  {mod.SYSTEM}: " + ", ".join(f"{g}={c[g]}" for g in mod.GROUPS))
    if lk and len({c[g] for g in mod.GROUPS}) > 1:
        errs.append(f"{mod.SYSTEM}: Likert items unbalanced across groups -> "
                    + ", ".join(f"{g}={c[g]}" for g in mod.GROUPS))

# ---- Likert polarity (rule 7 of the Likert memo: 20-30% inverse) ----
# Inverse items are DOCUMENTATION-ONLY metadata. Nothing is flipped before the
# Random Forest; the tree learns that low ordinal values predict the group.
print(f"\nLikert polarity per conjunto (target {INVERSE_MIN:.0%}-{INVERSE_MAX:.0%} inversa):")
any_likert = False
_inv_bank = []
for mod in MODULES:
    lk = [q for q in questions if q["system"] == mod.SYSTEM and q["qtype"] == "likert"]
    if not lk:
        continue
    any_likert = True
    inv = [q for q in lk if q["polarity"] == "inversa"]
    share = len(inv) / len(lk)
    print(f"  {mod.SYSTEM:36} {len(inv):>3}/{len(lk):<3} inversa  {share:5.0%}")
    # 2026-09-14: la cuota de inversas se evalúa a NIVEL BANCO, no por conjunto.
    # Con 4 Likert por grupo, un conjunto sólo puede dar 0%, 8%, 17%, 25%... y
    # además hay conjuntos donde un grupo no admite inversa limpia (regla 7b):
    # en Horneviano, Retraída no la admite porque su opuesto ES Asertiva. Exigir
    # 20-30% por conjunto obliga a escribir inversas que fallan la cobertura-3.
    if not (INVERSE_MIN <= share <= INVERSE_MAX):
        print(f"      (fuera de {INVERSE_MIN:.0%}-{INVERSE_MAX:.0%} en este conjunto "
              f"— la cuota se evalúa a nivel banco, ver abajo)")
    _inv_bank.append((len(inv), len(lk)))
    # inverse items should not all pile into one group
    per_group = collections.Counter(q["groups"][0] for q in inv)
    if inv and len(per_group) == 1 and len(inv) > 1:
        warns.append(f"{mod.SYSTEM}: all {len(inv)} inverse Likert items are in "
                     f"{list(per_group)[0]} — spread them across the three groups")
if _inv_bank:
    _i = sum(a for a, _ in _inv_bank); _t = sum(b for _, b in _inv_bank)
    _share = _i / _t
    print(f"  {'BANCO (cuota efectiva)':36} {_i:>3}/{_t:<3} inversa  {_share:5.0%}")
    if not (INVERSE_MIN <= _share <= INVERSE_MAX):
        warns.append(f"banco: {_share:.0%} Likert inversa ({_i}/{_t}), outside "
                     f"{INVERSE_MIN:.0%}-{INVERSE_MAX:.0%}")
if not any_likert:
    print("  (no Likert items in this build)")

# every scenario item must cover each group exactly once
for q in questions:
    if q["qtype"] == "scenario":
        mod = next(m for m in MODULES if m.SYSTEM == q["system"])
        if sorted(q["groups"]) != sorted(mod.GROUPS):
            errs.append(f"{q['id']} does not cover each group exactly once: {q['groups']}")

# ---- type_coverage: per-type reachability within each conjunto (rule 9) ----
# Scenario items only. A Likert item offers five options all carrying one group,
# so it reaches only that group's three types by construction; including them
# would report a floor violation that is a property of the format, not a defect.
errs.extend(cov_errs)

print("\nType reachability per conjunto (scenario items — floor %.0f%%):" % (REACH_FLOOR * 100))
for mod in MODULES:
    sc = [q for q in questions if q["system"] == mod.SYSTEM and q["qtype"] == "scenario"]
    n = len(sc)
    print(f"  {mod.SYSTEM}  ({n} items)")
    for grp in mod.GROUPS:
        cells = []
        for t in mod.GROUP_TYPES[grp]:
            hits = sum(1 for q in sc if any(t in c for c in q["coverage"]))
            share = hits / n if n else 0.0
            cells.append(f"{t}:{hits:>3}/{n} {share:5.0%}")
            if n and share < REACH_FLOOR:
                errs.append(
                    f"{mod.SYSTEM}: type {t} ({grp}) reachable in only {share:.0%} "
                    f"of scenario items — floor is {REACH_FLOOR:.0%}")
        print(f"    {grp:22} " + "   ".join(cells))

# how much of the bank departs from pure group-level phrasing
flavoured = [r for r in rows if r["format"] == "scenario"
             and len(r["type_coverage"].split("|")) < 3]
print(f"\nOptions narrower than full group-level: {len(flavoured)} "
      f"of {sum(1 for r in rows if r['format'] == 'scenario')} scenario options")
for r in flavoured:
    print(f"    {r['question_id']}  {r['group_label']:14} -> {r['type_coverage']:8} "
          f"{r['option_text'][:44]}")

# label vocabulary check
valid = set()
for m in MODULES:
    valid |= set(m.GROUPS)
for r in rows:
    if r["group_label"] not in valid:
        errs.append(f"{r['question_id']}: unknown group_label {r['group_label']!r}")

# duplicate prompt / duplicate option detection
dupes = [p for p, n in collections.Counter(q["prompt"] for q in questions).items() if n > 1]
for d in dupes:
    errs.append(f"duplicate prompt: {d[:60]}")

opt_dupes = [o for o, n in collections.Counter(
    (r["prompt"], r["option_text"]) for r in rows).items() if n > 1]
for o in opt_dupes:
    errs.append(f"duplicate option within a question: {o[1][:40]}")

# stray non-ascii / typo sentinels
for r in rows:
    for field in ("prompt", "option_text"):
        if "%" in r[field]:
            errs.append(f"{r['question_id']}: stray '%' in {field}")

# ---- option length bounds (scenario options only) ----
# The 6-14 rule lived only in prose through v1-v4, which is part of why items
# drifted. Bounds are now 4-20: 4 admits "Que fuiste una carga" (R4 Rechazo),
# 20 admits the longest options the v4 review approved.
print(f"\nOption length — scenario options {MIN_WORDS}-{MAX_WORDS} words, "
      f"Likert statements >={LIKERT_MIN_WORDS} (sin techo; se informa >{LIKERT_REPORT_WORDS}):")
lens = [len(r["option_text"].split()) for r in rows if r["format"] == "scenario"]
if lens:
    print(f"  scenario  min {min(lens)}   max {max(lens)}   mean {sum(lens)/len(lens):.1f}")
# A Likert item's text lives in the PROMPT (the statement); its five options are
# the fixed scale labels, so the bound applies to the prompt, once per question.
lk_lens = [len(q["prompt"].split()) for q in questions if q["qtype"] == "likert"]
if lk_lens:
    print(f"  likert    min {min(lk_lens)}   max {max(lk_lens)}   mean {sum(lk_lens)/len(lk_lens):.1f}")
for r in rows:
    if r["format"] != "scenario":
        continue
    n = len(r["option_text"].split())
    if n < MIN_WORDS or n > MAX_WORDS:
        errs.append(f"{r['question_id']}: option is {n} words "
                    f"(bounds {MIN_WORDS}-{MAX_WORDS}): {r['option_text'][:52]!r}")
for q in questions:
    if q["qtype"] != "likert":
        continue
    n = len(q["prompt"].split())
    if n < LIKERT_MIN_WORDS:
        errs.append(f"{q['id']}: Likert statement is {n} words "
                    f"(floor {LIKERT_MIN_WORDS}): {q['prompt'][:52]!r}")
    elif n > LIKERT_REPORT_WORDS:
        print(f"    largo  {n:>2}  {q['id']} — {q['prompt'][:60]}"
              "   (informativo: sin techo, revisar una sola proposición)")
at_bound = [r for r in rows if r["format"] == "scenario"
            and len(r["option_text"].split()) in (MIN_WORDS, MAX_WORDS)]
for r in at_bound:
    print(f"    exactly {len(r['option_text'].split()):>2}  {r['question_id']} "
          f"[{r['group_label']}] {r['option_text'][:46]}")

# ---- lexical saturation within a group ----
def _words(text):
    t = unicodedata.normalize("NFD", text.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return {w for w in re.findall(r"[a-zñ]+", t) if w not in STOP and len(w) > 4}


print(f"\nLexical saturation per group (content word in >={SATURATION_SHARE:.0%} "
      f"of that group's scenario options):")
for mod in MODULES:
    for grp in mod.GROUPS:
        opts = [r["option_text"] for r in rows
                if r["grouping_system"] == mod.SYSTEM and r["format"] == "scenario"
                and r["group_label"] == grp]
        if not opts:
            continue
        c = collections.Counter()
        for o in opts:
            for w in _words(o):
                c[w] += 1
        hot = [(w, n) for w, n in c.most_common()
               if n >= SATURATION_MIN and n / len(opts) >= SATURATION_SHARE]
        _ok = CONSTRUCT_WORDS.get((mod.SYSTEM, grp), set())
        # Una palabra sólo es proxy si DISCRIMINA. `poder` aparecía en 6 de 24
        # Retraídas (25%) y disparaba advertencia — pero está en 5 de 24 Asertivas
        # (21%) del mismo conjunto: no distingue nada, es un auxiliar. Se compara
        # la tasa del grupo contra la mayor de los otros dos del conjunto y se
        # exige el DOBLE para advertir; por debajo va como informativo con la
        # comparación al lado. (Decisión del revisor, 2026-09-20.)
        def _rate_elsewhere(word):
            best = 0.0
            for other in mod.GROUPS:
                if other == grp:
                    continue
                o2 = [r["option_text"] for r in rows
                      if r["grouping_system"] == mod.SYSTEM and r["format"] == "scenario"
                      and r["group_label"] == other]
                if o2:
                    best = max(best, sum(1 for t in o2 if word in _words(t)) / len(o2))
            return best

        real, weak, declared = [], [], []
        for w, n in hot:
            if w in _ok:
                declared.append((w, n, 0.0))
                continue
            other = _rate_elsewhere(w)
            (real if n / len(opts) >= 2 * max(other, 1e-9) else weak).append((w, n, other))
        if real:
            print(f"  {mod.SYSTEM[:26]:26} {grp:14} " +
                  ", ".join(f"{w} {n}/{len(opts)} (otros grupos {o:.0%})"
                            for w, n, o in real))
            for w, n, o in real:
                warns.append(f"{mod.SYSTEM} / {grp}: '{w}' in {n} of {len(opts)} options "
                             f"({n/len(opts):.0%} vs {o:.0%} en los otros grupos) "
                             f"— lexicalised proxy risk")
        if weak:
            print(f"  {mod.SYSTEM[:26]:26} {grp:14} " +
                  ", ".join(f"{w} {n}/{len(opts)} = {n/len(opts):.0%} vs {o:.0%} en los "
                            f"otros grupos" for w, n, o in weak) +
                  "   (no discrimina — informativo)")
        if declared:
            print(f"  {mod.SYSTEM[:26]:26} {grp:14} " +
                  ", ".join(f"{w} {n}/{len(opts)}" for w, n, _ in declared) +
                  "   (palabra-constructo declarada — informativo, no advertencia)")
if not any(w.endswith("lexicalised proxy risk") for w in warns):
    print("  none")

# ---- opening-word monotony ----
#
# 2026-09-12: `que` is EXEMPT when the stem is copular.
#
# Rule 15 in the design notes, added by the reviewer after this check damaged a whole batch.
# Stems like "lo que más te pesa es" / "lo que menos tolerarías es" are copular sentences waiting
# for a complement, and in Spanish that complement is a noun phrase or a subordinate clause
# introduced by `que`. So `Que + subjuntivo` is not a syntactic template — it is the grammatically
# obligatory completion. This check counted first words and read the complementiser as monotony.
#
# Acting on the flag cost ten options in the Armónico batch: every single option the reviewer
# flagged for unclarity or for not answering the stem was one rewritten to escape `Que`. The check
# was measuring the stem's grammar, not the writer's repetition.
#
# The real template risk lives in content words (see the lexical-saturation check above), so the
# exemption is narrow: only `que`, and only for options whose own stem is copular.
COPULAR_STEM = r"(^|\b)lo (que|primero)\b[^:]*\b(es|seria|sera)\s*:?\s*$"


def _plain_stem(text):
    t = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn").strip()

print(f"\nOpening-word concentration per conjunto (flag at >={OPENING_SHARE:.0%}"
      f" · 'que' exempt after a copular stem, rule 15):")
for mod in MODULES:
    pairs = [(r["option_text"], r["prompt"]) for r in rows
             if r["grouping_system"] == mod.SYSTEM and r["format"] == "scenario"]
    if not pairs:
        continue
    def _first(o):
        return "".join(ch for ch in unicodedata.normalize("NFD", o.split()[0].lower())
                       if unicodedata.category(ch) != "Mn")
    exempt = sum(1 for o, p in pairs
                 if o.split() and _first(o) == "que"
                 and re.search(COPULAR_STEM, _plain_stem(p)))
    first = collections.Counter(_first(o) for o, p in pairs if o.split()
                                and not (_first(o) == "que"
                                         and re.search(COPULAR_STEM, _plain_stem(p))))
    if not first:
        print(f"  {mod.SYSTEM[:34]:34} todas las aperturas exentas (rule 15)")
        continue
    top, n = first.most_common(1)[0]
    tot = len(pairs)
    print(f"  {mod.SYSTEM[:34]:34} {len(first):>3} aperturas distintas / {tot} "
          f"opciones · más frecuente: '{top}' {n}"
          + (f" · {exempt} 'que' exentas" if exempt else ""))
    if n / tot >= OPENING_SHARE:
        warns.append(f"{mod.SYSTEM}: '{top}' opens {n} of {tot} options "
                     f"({n/tot:.0%}) — syntactic template risk")

# ---- propositional-frame template (2026-09-13) ----
#
# The defect the reviewer named after the second Armónico batch, and the one no existing check
# could see:
#
#   "Ya me resulta hasta gracioso que se repita tantas veces la misma estructura de afirmación
#    para Positiva: «Que X no opaque lo bueno de Y». La idea está bien, siempre y cuando no se
#    formule de la misma manera CADA VEZ. En algún momento eran más precisas y claras, pero la
#    repetición en exceso hace que deje de elegirla."
#
# Measured: that frame went from 2 of 12 Positiva options in batch 1 to 7 of 7 in batch 2.
# Jaccard sees nothing — every instance has different content words, so pairwise similarity is
# near zero. The opening-word check sees nothing either, because `que` is exempt under rule 15.
# What repeats is the SHAPE of the proposition, carried by its negation/contrast markers.
#
# So the frame is the ordered sequence of those markers, and content words are ignored entirely.
# A group whose options all share one frame is a group the respondent reads as one option.
#
# Note the interaction worth remembering: the frame exploded in the batch where rule 15 first
# applied. Removing the `Que` rewrite was correct — the reviewer confirmed the openings go
# unnoticed — but it also removed an accidental brake on this. The fix is this check, not
# reinstating a rule that broke ten options.
FRAME_MARKERS = {"no", "sin", "todavia", "ya", "aun", "aunque", "tampoco", "nunca", "nada"}
FRAME_LEN = 2
FRAME_SHARE = 0.40

print(f"\nPropositional frame per group (negation/contrast markers, "
      f"flag at >={FRAME_SHARE:.0%} of a group's scenario options):")


def _frame(text):
    t = unicodedata.normalize("NFD", text.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    ws = [w for w in re.findall(r"[a-z]+", t) if w in FRAME_MARKERS]
    return " ".join(ws[:FRAME_LEN]) if ws else None


for mod in MODULES:
    for g in mod.GROUPS:
        opts = [r["option_text"] for r in rows
                if r["grouping_system"] == mod.SYSTEM and r["group_label"] == g
                and r["format"] == "scenario"]
        if len(opts) < 6:
            continue
        c = collections.Counter(f for f in (_frame(o) for o in opts) if f)
        if not c:
            continue
        top, n = c.most_common(1)[0]
        share = n / len(opts)
        mark = "  <-- REVISAR" if share >= FRAME_SHARE else ""
        print(f"  {mod.SYSTEM[:24]:24} {g:14} «{top}» {n}/{len(opts)} = {share:.0%}{mark}")
        if share >= FRAME_SHARE:
            warns.append(f"{mod.SYSTEM} / {g}: propositional frame «{top}» in {n} of "
                         f"{len(opts)} options ({share:.0%}) — same shape, different words")

# ---- concessive-connector template ----
def _plain(text):
    t = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


print(f"\nConcessive connectors per conjunto (flag at >={CONCESSIVE_SHARE:.0%} of items):")
for mod in MODULES:
    sc = [r["option_text"] for r in rows
          if r["grouping_system"] == mod.SYSTEM and r["format"] == "scenario"]
    lk = [q["prompt"] for q in questions
          if q["system"] == mod.SYSTEM and q["qtype"] == "likert"]
    for label, texts in (("escenario", sc), ("likert", lk)):
        if not texts:
            continue
        hits = [t for t in texts if re.search(CONCESSIVE, _plain(t))]
        share = len(hits) / len(texts)
        dbl = sum(1 for t in texts if len(re.findall(CONCESSIVE, _plain(t))) > 1)
        print(f"  {mod.SYSTEM[:26]:26} {label:9} {len(hits):>3}/{len(texts):<3} {share:5.0%}"
              + (f"   ({dbl} con dos en la misma frase)" if dbl else ""))
        if share >= CONCESSIVE_SHARE:
            warns.append(f"{mod.SYSTEM} / {label}: concessive connector in "
                         f"{len(hits)} of {len(texts)} ({share:.0%}) — argumentative "
                         f"template risk")
        if dbl:
            warns.append(f"{mod.SYSTEM} / {label}: {dbl} item(s) use two concessive "
                         f"connectors in one sentence")

# Template repetition WITHIN one item.
#
# Added 2026-09-10. The opening-word check above scans a whole conjunto and so is blind to
# a single block whose options all start the same way. Horneviano row 9 shipped with two of
# three options opening "Que el reparto te deje" and every existing check passed it.
# Two of three options sharing an opening is a within-block cue: the respondent stops reading
# the options as three different propositions and starts reading them as variants of one.
#
# WARN ONLY, never an error, per the 2026-09-10 decision. Legitimate cases exist — three
# options that must share a time horizon often share a connective, and the fix can cost more
# in construct terms than the repetition costs in reading terms.
FUNC_WORDS = {
    "a", "al", "antes", "ante", "apenas", "aunque", "bajo", "cada", "como", "con",
    "contra", "cuando",
    "de", "del", "desde", "despues", "donde", "durante", "el", "en", "entre", "esa", "ese",
    "eso", "esta", "este", "esto", "hacia", "hasta", "la", "las", "le", "les", "lo",
    "los", "me", "mi", "mientras", "mis", "muy", "nos", "o", "para", "pero", "por",
    "que", "recien", "se", "si", "sin", "sobre", "su", "sus", "te", "tras", "tu", "tus", "un",
    "una", "unas", "unos", "vez", "y", "ya",
}


print(f"\nRepeated opening within a single item (>= {ITEM_TEMPLATE_N} options of 3, "
      f"first {ITEM_TEMPLATE_WORDS} words):")
_item_tpl = 0
_by_item = collections.defaultdict(list)
for r in rows:
    if r["format"] == "scenario":
        _by_item[(r["question_id"], r["grouping_system"])].append(r["option_text"])
for (qid, system), texts in _by_item.items():
    if len(texts) < 3:
        continue
    heads = collections.Counter(" ".join(_plain(t).split()[:ITEM_TEMPLATE_WORDS])
                                for t in texts)
    # Rule 15 again: a bare shared `que` is the stem's obligatory complementiser, not a template.
    heads.pop("que", None)
    for head, n in heads.items():
        # Criterio unificado con C6 (2026-09-20, decisión del revisor): la apertura
        # compartida tiene que incluir AL MENOS UNA palabra de contenido. Sin este
        # filtro el chequeo marca «que se…», «en un…», «si un…» — conectores,
        # preposiciones y artículos que no cargan nada. Con él marca «tu capacidad
        # de…» y «sentir por dentro…», que son moldes de verdad.
        # Y es ADVERTENCIA, nunca error: nada se reescribe por este chequeo.
        if head and not [w for w in head.split() if w not in FUNC_WORDS]:
            continue
        if n >= ITEM_TEMPLATE_N and head:
            _item_tpl += 1
            print(f"  {qid:6} {system[:22]:22} \"{head}…\" x{n}/{len(texts)}")
            warns.append(f"{qid} ({system}): {n} of {len(texts)} options open with "
                         f"\"{head}…\" — within-block template")
if not _item_tpl:
    print("  ninguno")

# ---- C6. Apertura repetida dentro de un lote Likert -------------------------
#
# La Enmienda 1 fija el chequeo: "si dos afirmaciones de un mismo lote abren con
# las mismas dos palabras, el molde se volvió plantilla". El caso que lo generó
# fue «Aunque algo me entusiasme» — cuatro palabras de contenido, una construcción
# entera copiada en dos ítems de grupos distintos.
#
# REFINACIÓN (2026-09-20, aprobada por el revisor). Corrido crudo sobre el lote
# Centros v2 el chequeo marcó «Después de», «En un» y «Si un»: conectores,
# preposiciones y artículos, que no cargan nada y son las maneras que tiene el
# castellano de ubicar una escena en el tiempo — justo lo que el spec pide en las
# doce filas. Se exige que las dos palabras compartidas incluyan AL MENOS UNA de
# contenido. Con ese criterio el caso original sigue disparando («Aunque algo…»)
# y los tres conectores no.
#
# El chequeo vive acá y no en un script suelto: la versión anterior era mía, ad
# hoc, y me llevó a reescribir tres textos ya aprobados por una falsa alarma.


def _opening(text, n=3):
    return tuple(_plain(text).split()[:n])


print("\nApertura repetida dentro de un lote Likert "
      "(3 palabras; sólo si incluyen una de contenido):")
_open_hits = 0
for mod in MODULES:
    lik = [(q["id"], q["prompt"]) for q in questions
           if q["system"] == mod.SYSTEM and q["qtype"] == "likert"]
    seen = collections.defaultdict(list)
    for qid, text in lik:
        seen[_opening(text)].append(qid)
    for head, ids in sorted(seen.items()):
        if len(ids) < 2:
            continue
        carga = [w for w in head if w not in FUNC_WORDS]
        if not carga:
            print(f"  {mod.SYSTEM[:26]:26} «{' '.join(head)}» en {', '.join(ids)} "
                  f"— sólo palabras funcionales, no es plantilla")
            continue
        _open_hits += 1
        warns.append(f"{mod.SYSTEM}: «{' '.join(head)}» abre {len(ids)} afirmaciones "
                     f"({', '.join(ids)}) — molde vuelto plantilla")
        print(f"  {mod.SYSTEM[:26]:26} «{' '.join(head)}» en {', '.join(ids)}   <-- REVISAR")
if not _open_hits:
    print("  ninguna plantilla — las repeticiones que hay son sólo de palabras funcionales")

# Stem checks.
#
# Added 2026-09-10. Three of twelve stems in the Horneviano batch drew objections and no
# check existed that looked at a stem at all — everything scanned option_text. Two defects,
# both from that batch:
#
#   1. Unnamed domain object. "Cuando estás armando algo junto con otra gente" and "cuánto
#      poner en un asunto ajeno" both got the same annotation: qué algo / cuánto de qué.
#      The respondent has to invent the situation, and each one invents a different one.
#   2. Valence mismatch. "lo primero que pesa" reads as burden in Spanish. That is correct in
#      a negative domain (rows 10 and 12) and wrong in a neutral one (row 6), so the flag is
#      the pairing, not the word.
#
# Both are WARN. Neither can be decided without reading the domain, and the point of the
# check is to put the stem in front of a human, not to rule on it.
print("\nStem checks (warn only — every hit needs a human reading of the domain):")
_stem_hits = 0
_seen_stems = set()
for q in questions:
    # Likert prompts are statements to be rated, not stems — they have no domain to read
    # and the burden-verb heuristic misfires on them ("me pesa sostener un ritmo…").
    if q["qtype"] != "scenario":
        continue
    stem = q.get("prompt", "")
    if not stem or stem in _seen_stems:
        continue
    _seen_stems.add(stem)
    p = _plain(stem)
    if re.search(VAGUE_OBJECT, p):
        _stem_hits += 1
        print(f"  objeto sin nombrar   {q['system'][:20]:20} {stem[:66]}")
        warns.append(f"{q['system']}: stem names no concrete object — \"{stem[:60]}\"")
    if re.search(NEGATIVE_STEM_VERB, p) and not re.search(NEGATIVE_DOMAIN, p):
        _stem_hits += 1
        print(f"  valencia a revisar   {q['system'][:20]:20} {stem[:66]}")
        warns.append(f"{q['system']}: stem uses a burden verb in a domain with no negative "
                     f"marker — \"{stem[:60]}\"")
if not _stem_hits:
    print("  ninguno")

# position must not be confounded with group_label
if not CHECK_POSITION:
    print("\nOption position x group_label: SKIPPED (prototype mode — see reason above)")
print("\nOption position x group_label (scenario items — must NOT be diagonal):"
      if CHECK_POSITION else "", end="")
for mod in (MODULES if CHECK_POSITION else []):
    tab = collections.Counter()
    for r in rows:
        if r["grouping_system"] == mod.SYSTEM and r["format"] == "scenario":
            tab[(r["display_order"], r["group_label"])] += 1
    print(f"  {mod.SYSTEM}")
    print("      pos " + "".join(f"{g:>16}" for g in mod.GROUPS))
    for pos in (1, 2, 3):
        print(f"      {pos:>3} " + "".join(f"{tab[(pos,g)]:>16}" for g in mod.GROUPS))
    for pos in (1, 2, 3):
        for g in mod.GROUPS:
            n = tab[(pos, g)]
            if n == 0:
                errs.append(f"{mod.SYSTEM}: group {g} never appears at position {pos}")

# ---------------------------------------------------------------------------
# Chequeos de la pasada de consolidación (2026-09-18).
# Los cinco salieron de defectos reales encontrados lote por lote y vivían en
# notas. Umbrales fijados en [[Plan de la pasada de consolidación]] ANTES de
# correrlos por primera vez sobre el banco entero.
# ---------------------------------------------------------------------------

# --- C1. Tasa de demostrativo neutro -------------------------------------
# `eso`/`esto`/`aquello` son, por gramática, referentes que no llevan
# sustantivo: "ese trabajo" está bien, "de eso" no puede estarlo. Costó siete
# filas en Relaciones lote 1 (19% del set perdedor contra 3% del ganador).
# Alerta de TASA, no de opción: hay opciones aprobadas que lo usan.
NEUTRO_RX = re.compile(r"\b(eso|esto|aquello)\b")
NEUTRO_SHARE = 0.10
print(f"\nDemostrativo neutro (alerta sobre {NEUTRO_SHARE:.0%} de las opciones de un conjunto):")
for mod in MODULES:
    opts = [r for r in rows if r["grouping_system"] == mod.SYSTEM and r["format"] == "scenario"]
    hits = [r for r in opts if NEUTRO_RX.search(_plain(r["option_text"]))]
    if not opts:
        continue
    share = len(hits) / len(opts)
    mark = "  <-- REVISAR" if share >= NEUTRO_SHARE else ""
    print(f"  {mod.SYSTEM:36} {len(hits):>2}/{len(opts):<3} {share:5.0%}{mark}")
    if share >= NEUTRO_SHARE:
        warns.append(f"{mod.SYSTEM}: demostrativo neutro en {share:.0%} de las opciones")
    for r in hits:
        print(f"      {r['question_id']} [{r['group_label']}] {r['option_text'][:60]}")
    # Desglose POR GRUPO — informativo, nunca advertencia (decisión del revisor,
    # 2026-09-20). El promedio del conjunto esconde la concentración: Horneviano
    # entero da 8% y pasa, pero Complaciente sola da 21% y Retraída 0%. Un
    # pronombre que aparece en un grupo y en otro no es un predictor, aunque el
    # conjunto esté debajo del umbral. No dispara nada: se mira al revisar.
    _porgrupo = []
    for grp in mod.GROUPS:
        og = [r for r in opts if r["group_label"] == grp]
        hg = [r for r in og if NEUTRO_RX.search(_plain(r["option_text"]))]
        if og:
            _porgrupo.append(f"{grp} {len(hg)}/{len(og)} = {len(hg)/len(og):.0%}")
    print(f"      por grupo (informativo): {' · '.join(_porgrupo)}")

# --- C2. Solapamiento entre grupos DENTRO del mismo ítem -------------------
# check_neighbors compara mismo-grupo y contra el banco; el par Apego/Frustración
# de la fila 5 de Relaciones (dos opciones del MISMO ítem diciendo lo mismo) no lo
# miraba nadie. Sólo alerta: Jaccard no vio el caso original (0.12) — el defecto
# real era una premisa compartida, que es de comprensión y no de léxico.
INTRA_ITEM_J = 0.30
print(f"\nSolapamiento entre grupos dentro del ítem (alerta >= {INTRA_ITEM_J}):")
_intra = []
for q in questions:
    if q["qtype"] != "scenario":
        continue
    opts = [r for r in rows if r["question_id"] == q["id"]]
    for a, b in itertools.combinations(opts, 2):
        x, y = _words(a["option_text"]), _words(b["option_text"])
        j = len(x & y) / len(x | y) if (x | y) else 0.0
        _intra.append((j, q["id"], a["group_label"], b["group_label"]))
_intra.sort(reverse=True)
for j, qid, ga, gb in _intra[:3]:
    print(f"    máx {j:.2f}  {qid}  {ga} / {gb}")
for j, qid, ga, gb in _intra:
    if j >= INTRA_ITEM_J:
        warns.append(f"{qid}: {ga}/{gb} solapan {j:.2f} dentro del mismo ítem")

# --- C3. Terna de facetas única por ítem · C4. la opción no nombra su faceta ---
# Desbloqueados el 2026-09-20 con qbank/facets.json, que extract_facets.py saca
# de las tablas de los specs. C3 sale de las filas 9 y 13 de Relaciones, que
# compartían las tres facetas y nadie lo vio porque los conteos eran por grupo y
# nunca por terna. C4 sale de una Apego que decía "referencias" con faceta
# `referencia`: cuando la etiqueta se filtra a la prosa, el clasificador aprende
# la etiqueta. La cohorte v4.1 no tiene spec: sus facetas son inferidas y
# aprobadas, entran a C3 y quedan fuera de C4 (ver _INFERRED).
try:
    _FJ = json.load(io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "facets.json"), encoding="utf-8"))
    _FAC, _FSRC = _FJ["facets"], _FJ["sources"]
    _FINF = set(_FJ.get("inferred", []))
except Exception as _e:                                    # pragma: no cover
    _FAC, _FSRC, _FINF = {}, {}, set()
    print(f"\nfacets.json no disponible ({_e}) — C3 y C4 no corren")

_ALIAS = {"rel1": "rel", "rel2": "rel", "arm1": "arm", "arm2": "arm"}

# Facetas INFERIDAS (cohorte v4.1). C4 pregunta si la opción contiene una palabra
# de su faceta; en estas la faceta se dedujo LEYENDO la opción, así que la
# respuesta es sí por construcción y no mide nada. C3 sí corre: la unicidad de la
# terna no depende de cómo se nombró cada faceta.
_INFERRED = _FINF

# Ternas repetidas aceptadas, con el motivo. No es una lista para silenciar:
# la repetición se declaró en el spec ANTES de escribir la prosa y el revisor la
# leyó y la aceptó por escrito ("las filas 9 y 13 son suficientemente distintas").
ACCEPTED_TRIPLES = {
    ("Q120", "Q122"): "rel 09 y rel 13 — declarada en el spec v2 y aceptada al adjudicar",
    ("Q004", "Q010"): ("v4.1 C4 y lote1 04 — misma terna (posición/identidad/orientación) en dos "
                       "escenas distintas: trabajar en algo no elegido y convivir con gente no "
                       "elegida. Aceptada 2026-09-18: los ítems están bien instanciados y el "
                       "solapamiento léxico es 0.08/0.09/0.00 — la terna se comparte, la escena no. "
                       "Q004 está flojo y se revisa en el paso 6; la distancia debería crecer."),
}


def _facet_key(note):
    n = (note or "").split("·")[0].strip()
    if n in _FAC:                       # claves literales, p. ej. "v4.1 C1"
        return n
    m = re.match(r"([a-z0-9]+)\s+(\d+)([di])?$", n)
    if not m:
        return None
    return f"{_ALIAS.get(m.group(1), m.group(1))} {int(m.group(2)):02d}"


def _facets_for(note):
    return _FAC.get(_facet_key(note))


if _FAC:
    print("\nTerna de facetas única por ítem (C3) y opción que nombra su faceta (C4):")
    _seen_triples, _no_data = {}, collections.Counter()
    _inf_skipped = set()
    _c4 = []
    for q in questions:
        f = _facets_for(q.get("source"))
        if not f:
            _no_data[q["system"]] += 1
            continue
        if q["qtype"] == "scenario":
            triple = tuple(sorted((g, f.get(g, "")) for g in q["groups"]))
            key = (q["system"], triple)
            if key in _seen_triples:
                pair = tuple(sorted((q["id"], _seen_triples[key])))
                if pair in ACCEPTED_TRIPLES:
                    print(f"      terna repetida DECLARADA: {pair[0]} y {pair[1]} — "
                          f"{ACCEPTED_TRIPLES[pair]}")
                else:
                    errs.append(f"{q['id']} y {_seen_triples[key]}: misma terna de "
                                f"facetas en {q['system']}")
            else:
                _seen_triples[key] = q["id"]
        # C4 — la opción no puede contener una palabra de contenido de su faceta.
        # Las facetas inferidas no entran: se dedujeron leyendo la opción.
        if _facet_key(q.get("source")) in _INFERRED:
            _inf_skipped.add(q["id"])
            continue
        for r in (x for x in rows if x["question_id"] == q["id"]):
            lab = f.get(r["group_label"]) or f.get("_likert") or ""
            for w in _words(lab):
                if re.search(rf"\b{re.escape(w[:6])}", _plain(r["option_text"])):
                    _c4.append((q["id"], r["group_label"], lab, w, r["option_text"]))
                    break
    # Claves de facets.json que ningún ítem usa. No es cosmético: un conteo de
    # facetas hecho sobre las CLAVES en vez de sobre los ÍTEMS cuenta estas filas
    # muertas, y así nació el falso "compromiso x7, la concentración más alta del
    # banco" (2026-09-18). La faceta se cuenta por opción, nunca por fila de spec.
    _used = {_facet_key(q.get("source")) for q in questions}
    _orphans = sorted(k for k in _FAC if k not in _used)
    if _orphans:
        warns.append(f"facets.json: {len(_orphans)} claves que ningún ítem usa "
                     f"({', '.join(_orphans[:6])}) — specs superseded")
        print(f"  claves de faceta huérfanas: {len(_orphans)} -> "
              f"{', '.join(_orphans)}")
    print(f"  cubiertos: {len(questions) - sum(_no_data.values())} de {len(questions)} ítems")
    if _no_data:
        print("  sin faceta declarada (cohorte sin spec): " +
              ", ".join(f"{k[:22]} {v}" for k, v in _no_data.items()))
    print(f"  C3 · ternas repetidas no declaradas: "
          f"{sum(1 for e in errs if 'misma terna' in e)}")
    # C4 se mide como TASA por faceta, no como lista de casos: que una opción use
    # la palabra de su faceta una vez es español; que la usen TODAS las opciones
    # de esa faceta es la etiqueta convertida en predictor. Contar casos sueltos
    # daba 30 hits y ninguno era el defecto.
    _tot4, _hit4 = collections.Counter(), collections.Counter()
    for qid, grp, lab, w, txt in _c4:
        _hit4[(grp, lab)] += 1
    for q in questions:
        f = _facets_for(q.get("source"))
        if not f:
            continue
        for r in (x for x in rows if x["question_id"] == q["id"]):
            lab = f.get(r["group_label"]) or f.get("_likert") or ""
            if lab:
                _tot4[(r["group_label"], lab)] += 1
    _bad4 = [(k, _hit4[k], _tot4[k]) for k in _hit4
             if _tot4[k] >= 2 and _hit4[k] == _tot4[k]]
    if _inf_skipped:
        print(f"  C4 · excluidos {len(_inf_skipped)} ítems de faceta inferida "
              f"(la faceta se dedujo de la opción — el chequeo sería circular)")
    print(f"  C4 · facetas cuyas opciones la nombran TODAS: {len(_bad4)}"
          f"   (casos sueltos: {len(_c4)}, informativo)")
    for (grp, lab), h, t in _bad4:
        print(f"      {grp} «{lab}» -> {h}/{t}")
        warns.append(f"{grp} / faceta «{lab}»: la nombran {h} de {t} opciones — "
                     f"la etiqueta se volvió predictor")

# --- C5. Expresión keyeada a un grupo que migra a otro conjunto -----------
# `te toca` aparece 4 veces en el banco y las 4 en Horneviano-Complaciente: es
# el marcador léxico de ese grupo. El riesgo NO es que se concentre —eso es
# saturación, y ya lo mira el chequeo léxico— sino que una expresión keyeada a
# un grupo aparezca en OTRO conjunto: ahí el ítem queda leído por dos sistemas
# de agrupamiento y correlaciona dos clasificadores que deben ser independientes.
# Por eso se exige, además de concentración, presencia fuera del conjunto dueño.
NGRAM_MIN, NGRAM_CONC = 3, 0.80
print(f"\nExpresión keyeada a un grupo y usada fuera de su conjunto "
      f"(>= {NGRAM_MIN} apariciones, >= {NGRAM_CONC:.0%} en un grupo, y al menos una fuera):")
_ng = collections.defaultdict(collections.Counter)
for r in rows:
    if r["format"] != "scenario":
        continue
    ws = _plain(r["option_text"]).split()
    for n in (2, 3):
        for i in range(len(ws) - n + 1):
            g = " ".join(ws[i:i + n])
            if all(w in STOP for w in g.split()):
                continue
            _ng[g][(r["grouping_system"], r["group_label"])] += 1
_flagged = []
for g, c in _ng.items():
    tot = sum(c.values())
    if tot < NGRAM_MIN:
        continue
    (sysgrp, n) = c.most_common(1)[0]
    outside = sum(v for k, v in c.items() if k[0] != sysgrp[0])
    if n / tot >= NGRAM_CONC and outside:
        _flagged.append((outside, n, tot, g, sysgrp))
_flagged.sort(reverse=True)
if not _flagged:
    print("    ninguna — no hay expresión keyeada a un grupo usada en otro conjunto")
for outside, n, tot, g, sysgrp in _flagged[:12]:
    print(f"    {n}/{tot} en {sysgrp[0][:24]}/{sysgrp[1]}, {outside} fuera  ->  '{g}'")
    warns.append(f"expresión '{g}' keyeada a {sysgrp[1]} y usada {outside} vez/veces en otro conjunto")

# Servicio de consulta para la redacción: qué expresiones YA están keyeadas.
# No es una alerta; es lo que hay que consultar antes de escribir una opción.
_keyed = sorted(((sum(c.values()), g, c.most_common(1)[0][0])
                 for g, c in _ng.items()
                 if sum(c.values()) >= NGRAM_MIN
                 and c.most_common(1)[0][1] / sum(c.values()) >= NGRAM_CONC),
                reverse=True)[:15]
print(f"\n  Expresiones ya keyeadas a un grupo (consultar antes de reusarlas):")
for tot, g, sysgrp in _keyed:
    print(f"    {tot:>2}x  '{g}'  ->  {sysgrp[0][:26]} / {sysgrp[1]}")

print("\n" + "-" * 62)
if errs:
    print(f"ERRORS ({len(errs)}):")
    for e in errs:
        print("  x " + e)
else:
    print("ERRORS: none")
if warns:
    print(f"WARNINGS ({len(warns)}):")
    for w in warns:
        print("  ! " + w)
else:
    print("WARNINGS: none")

# ---------------- emit ----------------
OUT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__))) + "/"

for r in rows:
    r["prompt"] = accents.restore(r["prompt"])
    r["option_text"] = accents.restore(r["option_text"])

with open(OUT + BUILD_NAME + ".csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["question_id", "grouping_system", "question_type",
                                      "format", "prompt", "option_text", "group_label",
                                      "type_coverage", "polarity", "display_order",
                                      "origin"])
    w.writeheader()
    w.writerows(rows)

print(f"\nWrote CSV: {len(rows)} rows -> {BUILD_NAME}.csv")

if PROTOTYPE:
    # The markdown doc below is a bank review artifact — its header, status
    # section and composition table are all bank-specific. Emitting it for a
    # prototype would produce a misleading document.
    print("Markdown review doc: skipped (prototype mode)")
    sys.exit(1 if errs else 0)

# ---------------- markdown review doc ----------------
amb = sum(accents.count_ambiguous(q["prompt"]) for q in questions)
md = []
md.append("""---
aliases:
tags:
  - context/personal
  - context/uade
categories:
  - "[[Project Note]]"
topics:
created: "2026-08-17 19:30"
modified:
---

# NureonAI Question Bank v1.2

> Working artifact for [[Rework NureonAI questionnaire questions mapped to the four grouping systems]].
> Machine-readable companion: `NureonAI Question Bank v1.2.csv` (one row per question+answer pair,
> shaped for the `questions` / `answer_options` tables in [[PDR — NureonAI Data Model]]).

## Status

**Draft — not locked.** Two finishing passes required before this becomes `version: 1`, `is_active: true`:

1. **Diacritics.** Items were drafted without accents for pipeline safety, then auto-restored for
   words whose accented form is context-free (`más`, `también`, `-ción` nouns, voseo forms, etc.).
   Context-dependent tokens were deliberately left alone and need a human pass: **que/qué**,
   **como/cómo**, **cual/cuál**, **quien/quién**, **donde/dónde**, **si/sí**, **esta/está**.
   Interrogatives inside prompts are the main case. Opening question marks (`¿`) also still need adding.
2. **Human review of item quality** — especially the reworked items, against the originals in Anexo C.

## Composition

| | |
|---|---|
| Total questions | %d |
| Total question+answer pairs | %d (objective: ≥500) |
| Reworked from Anexo C | %d |
| Net-new | %d |
| Scenario / multiple-choice items | %d |
| Likert items (5 ordered options) | %d |
| Questions per grouping system | 50 / 50 / 50 / 50 |
| `group_label` balance within each system | even (verified programmatically) |

Every scenario item covers each of its system's three groups exactly once — verified in the build,
so no item can silently over-represent one group.

## Canonical vocabulary

Spanish labels are canonical, per §2.1.5.2–2.1.5.3 (Anexo C's English labels were a mistake):

| Conjunto | Grupos |
|---|---|
| Centros de Inteligencia | Cuerpo / Corazón / Mente |
| Conjunto Horneviano | Asertiva / Complaciente / Retraída |
| Conjunto Armónico | Positiva / Competente / Reactiva |
| Conjunto de Relaciones Objetales | Apego / Frustración / Rechazo |

## Design notes

- **Motivation over behaviour.** The rework consistently moves prompts from *what you do* to
  *what drives you* — the project's stated differentiator against trait/behaviour instruments.
  Many original Anexo C items asked for observable reactions; those were reframed.
- **Varied stems.** The original bank leaned on one repeated template per system
  ("Cuando te enfrentas a…", "Imagina que…", "¿Cómo…?"). Stems here are deliberately mixed so
  respondents can't pattern-match the question type before reading it.
- **`grouping_system` is authoring metadata, not a feature filter.** Per
  [[PDR — NureonAI 4-Classifier ML Design]], all four classifiers train on the full item vector.
- **Likert items** encode as `multiple_choice` with 5 ordered options, all carrying the statement's
  target `group_label`; the signal is the ordinal position.

---

""" % (len(questions), len(rows),
       sum(1 for q in questions if q["origin"] == "R"),
       sum(1 for q in questions if q["origin"] == "N"),
       sum(1 for q in questions if q["qtype"] == "scenario"),
       sum(1 for q in questions if q["qtype"] == "likert")))

for mod in MODULES:
    md.append(f"## {mod.SYSTEM}\n")
    sc = [q for q in questions if q["system"] == mod.SYSTEM and q["qtype"] == "scenario"]
    lk = [q for q in questions if q["system"] == mod.SYSTEM and q["qtype"] == "likert"]
    md.append(f"*{len(sc)} ítems de escenario · {len(lk)} ítems Likert*\n")
    md.append("| # | Origen | Pregunta | Respuesta | Grupo |")
    md.append("|---|---|---|---|---|")
    for q in sc:
        opts = [r for r in rows if r["question_id"] == q["id"]]
        for i, r in enumerate(opts):
            qid_c = q["id"] if i == 0 else ""
            org = ("Rework" if q["origin"] == "R" else "Nueva") if i == 0 else ""
            pr = q["prompt"] if i == 0 else ""
            md.append(f"| {qid_c} | {org} | {pr} | {r['option_text']} | {r['group_label']} |")
    md.append("\n### Ítems Likert\n")
    md.append("Escala de 5 puntos: Muy en desacuerdo · En desacuerdo · Neutral · De acuerdo · Muy de acuerdo\n")
    md.append("| # | Afirmación | Grupo |")
    md.append("|---|---|---|")
    for q in lk:
        md.append(f"| {q['id']} | {q['prompt']} | {q['groups'][0]} |")
    md.append("")

md.append("---\n\n## Reworked items — what changed\n")
md.append("| # | Conjunto | Cambio respecto de Anexo C |")
md.append("|---|---|---|")
for q in questions:
    if q["origin"] == "R":
        md.append(f"| {q['id']} | {q['system']} | {q['source']} |")
md.append("")

text = "\n".join(md)
text = accents.restore(text)

with open(OUT + "NureonAI Question Bank v1.2.md", "w", encoding="utf-8") as f:
    f.write(text)

print(f"Wrote markdown review doc ({len(text.splitlines())} lines)")
print(f"Context-dependent tokens left for human accent pass (prompts only): ~{amb}")
print(f"Wrote {len(questions)} questions across {len(by_sys)} grouping systems")
