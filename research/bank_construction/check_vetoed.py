# -*- coding: utf-8 -*-
"""Vetoed-phrase linter for the NureonAI question bank.

WHY THIS EXISTS
---------------
"Bronca" was vetoed in the v2 review, written down, and then walked straight back
into v4 C1. So did "tu manera de moverte". In both cases the correction existed,
was recorded, and nobody consulted it while drafting. That is a process failure,
not a judgement one, and it is exactly what a linter fixes.

The phrase list in vetoed.csv is compiled from the four per-conjunto memos:
    [[Centros de Inteligencia — Reglas de Redacción de Ítems]]
    [[Conjunto Horneviano — Reglas de Redacción de Ítems]]
    [[Conjunto Armónico — Reglas de Redacción de Ítems]]
    [[Conjunto de Relaciones Objetales — Reglas de Redacción de Ítems]]

SCOPING — THE IMPORTANT PART
----------------------------
Almost nothing is banned globally. Vetoes are attached to the GROUP they came
from, because the same words are correct elsewhere:

    "resolver"  -> vetoed in Frustración (contaminates Competente)
                   correct     in Competente
    "vuelvan a estar bien"
                -> vetoed in Apego (contaminates Positiva/9)
                   fine        as a Positiva option

A flat wordlist would flag correct items constantly, and a linter that cries wolf
gets ignored.

VETOES ARE ABOUT USAGES, NOT VOCABULARY
---------------------------------------
Three separate corrections have now landed on the same mistake — banning a word
when only one of its usages was ever the problem:

    "necesitar"  Relaciones rule 10 says outright that the word is fine; the
                 defect is an option that reduces to "no quiero depender".
    "moverte"    Removed from H2's stem for naturalness, then deliberately
                 chosen inside C1-Mente. Only "tu manera de moverte" was ever
                 objected to.
    "empujar"    Permitted in its literal sense. What was vetoed is the calque
                 of English "push" — "empujar hasta que...", "empujar más
                 fuerte" — so the pattern targets those constructions only.

Rule of thumb when adding entries: write the shortest phrase that is wrong in
EVERY context you can imagine it appearing. If you can think of a sentence where
it would be correct, the pattern is too short.

TIERS
-----
    register  -> ERROR. Near-zero false positives (bronca, bancar, empujar...).
    construct -> WARN.  Heuristic: a substring match does not prove the option is
                 8-flavoured. Reports for human judgement, never blocks.

USAGE
-----
    python3 check_vetoed.py                       # default bank, report-only
    python3 check_vetoed.py path/to.csv           # any built CSV
    python3 check_vetoed.py --strict              # construct hits also fail

Exit 1 if any register hit (or any hit under --strict).
"""
import csv, re, sys, os, unicodedata, collections

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(HERE)
DEFAULT_CSV = os.path.join(VAULT, "NureonAI Question Bank v1.2.csv")
LIST_CSV = os.path.join(HERE, "vetoed.csv")


def norm(s):
    """Lowercase and strip diacritics, so patterns can be written unaccented and
    still match accented item text (and vice versa)."""
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def load_rules(path=LIST_CSV):
    rules = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rules.append(dict(rule=r["rule"], tier=r["tier"], scope=r["scope"],
                              pattern=r["pattern"], note=r["note"],
                              rx=re.compile(norm(r["pattern"]))))
    return rules


def scan(rows, rules):
    """rows need 'option_text' and 'group_label'. Returns list of hits."""
    hits = []
    for r in rows:
        text = norm(r["option_text"])
        for rule in rules:
            if rule["scope"] != "ALL" and norm(rule["scope"]) != norm(r["group_label"]):
                continue
            if rule["rx"].search(text):
                hits.append((rule, r))
    return hits


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    strict = "--strict" in sys.argv
    path = os.path.abspath(args[0]) if args else DEFAULT_CSV
    if not os.path.exists(path):
        sys.exit(f"check_vetoed: no such file: {path}")

    rules = load_rules()
    with open(path, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["format"] == "scenario"]

    print(f"source    : {os.path.basename(path)}")
    print(f"rules     : {len(rules)} "
          f"({sum(1 for x in rules if x['tier']=='register')} register / "
          f"{sum(1 for x in rules if x['tier']=='construct')} construct)")
    print(f"options   : {len(rows)} scenario rows")
    print(f"mode      : {'STRICT (construct hits fail too)' if strict else 'register fails, construct warns'}\n")

    hits = scan(rows, rules)
    reg = [h for h in hits if h[0]["tier"] == "register"]
    con = [h for h in hits if h[0]["tier"] == "construct"]

    for label, group in (("REGISTER (error)", reg), ("CONSTRUCT (warning)", con)):
        if not group:
            continue
        print(f"{label} — {len(group)} hit(s)")
        for rule, r in sorted(group, key=lambda h: h[0]["rule"]):
            print(f"  {rule['rule']:9} {r['question_id']} [{r['group_label']}] "
                  f"{r['option_text'][:58]}")
            print(f"            pattern {rule['pattern']!r} — {rule['note']}")
        print()

    by_rule = collections.Counter(h[0]["rule"] for h in con)
    if by_rule:
        print("construct hits per rule (top 10):")
        for rule, n in by_rule.most_common(10):
            print(f"  {n:>3}  {rule}")
        print()

    if reg:
        print(f"FAIL — {len(reg)} register veto(es). These are non-negotiable.")
        return 1
    if strict and con:
        print(f"FAIL — {len(con)} construct veto(es) under --strict.")
        return 1
    print(f"PASS — no register vetoes." +
          (f" {len(con)} construct warning(s) to review." if con else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
