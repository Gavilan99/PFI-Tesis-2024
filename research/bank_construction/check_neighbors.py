# -*- coding: utf-8 -*-
"""Near-duplicate scan WITHIN a conjunto — the gap check_overlap.py leaves open.

WHY THIS EXISTS
---------------
check_overlap.py compares options across DIFFERENT conjuntos, because a phrase
keyed to two grouping systems correlates two supposedly independent classifiers.
It deliberately skips same-conjunto pairs with the comment "within-system overlap
is expected".

That is true for options of the same group across items — Frustración options will
share vocabulary — but it left three real defect classes uncovered:

  1. DOMAIN duplication: a new item's stem re-runs an existing item's situation.
  2. CROSS-FORMAT duplication: a Likert statement restates a scenario option of
     the same group.
  3. SAME-GROUP near-duplicate: two options for one group that say the same thing.

All three have now shipped in specs. On the Centros Likert spec all three inverse
items duplicated existing reference statements. On the Horneviano spec eight of
thirty items duplicated existing bank content — four domains and four Likert
statements. Both were caught by an external reviewer reading carefully, twice.
That is a job for a script.

USAGE
-----
    python3 check_neighbors.py --audit                  # scan the built bank
    python3 check_neighbors.py --audit path/to.csv
    python3 check_neighbors.py candidates.txt           # spec-time check

The candidates file is one string per line, optionally "Conjunto | Grupo | texto"
to restrict the comparison; a bare line is compared against the whole bank.
Exit 1 if anything lands at or above the threshold.
"""
import csv, re, sys, os, unicodedata, itertools

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(os.path.dirname(HERE), "NureonAI Prototype v4.1.csv")

THRESHOLD = 0.34      # Jaccard on content words
SHORT = 3             # skip texts with fewer content words than this

STOP = set("""que de la el los las un una y o a en se te lo le su tu vos no es mas más por para
con del al sin ya si como cuando mi me nos ese esa eso este esta esto muy tan ser estar hacer
tener todo toda todos algo cada dos ni son era hay solo bien mal cosa cosas lo""".split())


def words(text):
    t = unicodedata.normalize("NFD", text.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return {w for w in re.findall(r"[a-zñ]+", t) if w not in STOP and len(w) > 3}


def jac(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def load(path):
    """Returns (prompts, options) as lists of dicts with a precomputed word set."""
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    prompts, seen = [], set()
    for r in rows:
        if r["question_id"] in seen:
            continue
        seen.add(r["question_id"])
        prompts.append(dict(id=r["question_id"], sys=r["grouping_system"],
                            fmt=r["format"], text=r["prompt"], w=words(r["prompt"])))
    options = [dict(id=r["question_id"], sys=r["grouping_system"], fmt=r["format"],
                    grp=r["group_label"], text=r["option_text"], w=words(r["option_text"]))
               for r in rows if r["format"] == "scenario"]
    return prompts, options


# 2026-09-18 — PAR DE CONTROL. El ítem 44 de Relaciones existe en las dos
# polaridades sobre el MISMO anclaje: comparten el dominio a propósito, porque
# la única variable del experimento es la polaridad. Sin esta exención el par
# da FAIL en cada corrida por una coincidencia buscada, y un FAIL que se sabe
# falso es peor que no tener chequeo: enseña a ignorar la salida.
CONTROL_PAIRS = [("Q134", "Q135")]


def _is_control(x, y):
    a, b = x.get("id"), y.get("id")
    return any({a, b} == set(p) for p in CONTROL_PAIRS)


def audit(path):
    prompts, options = load(path)
    hits = []

    # 1. domain duplication — prompt vs prompt, same conjunto
    for x, y in itertools.combinations(prompts, 2):
        if x["sys"] != y["sys"] or len(x["w"]) < SHORT or len(y["w"]) < SHORT:
            continue
        j = jac(x["w"], y["w"])
        if j >= THRESHOLD and not _is_control(x, y):
            hits.append(("DOMINIO", j, x, y))

    # 2. same-group option near-duplicates
    for x, y in itertools.combinations(options, 2):
        if x["sys"] != y["sys"] or x["grp"] != y["grp"] or x["id"] == y["id"]:
            continue
        if len(x["w"]) < SHORT or len(y["w"]) < SHORT:
            continue
        j = jac(x["w"], y["w"])
        if j >= THRESHOLD:
            hits.append(("MISMO GRUPO", j, x, y))

    # 3. cross-format — a Likert statement against scenario options of its group.
    #    The Likert statement lives in the prompt; its group is on its rows.
    lk = [p for p in prompts if p["fmt"] == "likert"]
    with open(path, encoding="utf-8") as f:
        grp_of = {r["question_id"]: r["group_label"] for r in csv.DictReader(f)}
    for s in lk:
        for o in options:
            if s["sys"] != o["sys"] or grp_of.get(s["id"]) != o["grp"]:
                continue
            if len(s["w"]) < SHORT or len(o["w"]) < SHORT:
                continue
            j = jac(s["w"], o["w"])
            if j >= THRESHOLD:
                hits.append(("CROSS-FORMAT", j, s, o))

    print(f"bank      : {os.path.basename(path)}")
    print(f"prompts   : {len(prompts)} · opciones escenario: {len(options)}")
    print(f"threshold : Jaccard >= {THRESHOLD}, dentro del mismo conjunto\n")
    for kind, j, x, y in sorted(hits, key=lambda h: -h[1]):
        print(f"  [{kind}] {j:.2f}")
        print(f"     {x['id']}  {x['text'][:76]}")
        print(f"     {y['id']}  {y['text'][:76]}")
        print(f"     compartido: {', '.join(sorted(x['w'] & y['w']))}\n")
    if hits:
        print(f"FAIL — {len(hits)} par(es) por encima del umbral dentro de un mismo conjunto.")
        return 1
    print("PASS — sin duplicaciones internas.")
    return 0


def candidates(cand_path, bank_path):
    """Spec-time mode: nearest bank neighbour for each proposed string."""
    prompts, options = load(bank_path)
    pool = [dict(kind="prompt", **p) for p in prompts] + \
           [dict(kind=f"opción {o['grp']}", **o) for o in options]
    lines = [l.strip() for l in open(cand_path, encoding="utf-8") if l.strip()
             and not l.startswith("#")]
    print(f"candidatos: {len(lines)} · banco: {os.path.basename(bank_path)}")
    print(f"umbral    : {THRESHOLD}\n")
    worst = 0
    for line in lines:
        parts = [p.strip() for p in line.split("|")]
        sysname = parts[0] if len(parts) == 3 else None
        text = parts[-1]
        w = words(text)
        cand_pool = [p for p in pool if sysname is None or p["sys"] == sysname]
        scored = sorted(((jac(w, p["w"]), p) for p in cand_pool
                         if len(p["w"]) >= SHORT), key=lambda t: -t[0])
        if not scored:
            continue
        j, best = scored[0]
        worst = max(worst, j)
        flag = "  <-- REVISAR" if j >= THRESHOLD else ""
        print(f"  {j:.2f}{flag}")
        print(f"     nuevo   : {text[:76]}")
        print(f"     vecino  : {best['id']} [{best['kind']}] {best['text'][:66]}")
        if j >= THRESHOLD:
            print(f"     compartido: {', '.join(sorted(w & best['w']))}")
        print()
    return 1 if worst >= THRESHOLD else 0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--audit" in sys.argv:
        return audit(os.path.abspath(args[0]) if args else DEFAULT_CSV)
    if not args:
        sys.exit(__doc__)
    return candidates(os.path.abspath(args[0]), DEFAULT_CSV)


if __name__ == "__main__":
    sys.exit(main())
