# -*- coding: utf-8 -*-
"""Generates a targeted review list for the human diacritics pass.
Instead of eyeballing 499 'que' tokens, surface only those in syntactic
contexts where the interrogative (accented) form is likely."""
import csv, re, collections, io, os, sys

# Accepts a CSV path as argv[1]; defaults to the bank.
# It used to hardcode the bank path and ignore any argument, which meant passing
# it another file returned a plausible-looking review list for the WRONG file.
VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SRC = os.path.join(VAULT, "NureonAI Question Bank v1.2.csv")

args = [a for a in sys.argv[1:] if not a.startswith("--")]
SRC = os.path.abspath(args[0]) if args else DEFAULT_SRC
if not os.path.exists(SRC):
    sys.exit(f"accent_review: no such file: {SRC}")
OUT = os.path.join(os.path.dirname(SRC),
                   os.path.splitext(os.path.basename(SRC))[0] + " — Accent Review.md")

print(f"source : {os.path.basename(SRC)}")
print(f"output : {os.path.basename(OUT)}")

rows = list(csv.DictReader(io.open(SRC, encoding="utf-8")))

# verbs that introduce an indirect question -> following que/como/cual is accented
TRIGGER = r"(?:saber|sabés|sabes|entender|entendés|ver|ves|definir|defin[ií]s|preguntar|preguntás|" \
          r"preguntás|decidir|decid[ií]s|notar|notás|registrar|registrás|evaluar|evaluás|" \
          r"aclarar|mostrar|contar|explicar|imaginar|pensar|pensás|elegir|eleg[ií]s)"
PREP = r"(?:en|de|a|con|por|para|sobre|hacia|hasta|desde)"

PATTERNS = [
    ("interrogativa tras preposición",  rf"\b{PREP}\s+(que|cual|quien|donde)\b"),
    ("pregunta indirecta tras verbo",   rf"\b{TRIGGER}\s+(que|como|cual|cuanto|donde)\b"),
    ("qué + infinitivo",                r"\b(que)\s+\w+(?:ar|er|ir)\b"),
    ("inicio de cláusula interrogativa",r"(?:^|,\s*)(que|como|cual|cuanto|quien|donde)\s"),
]

hits = collections.defaultdict(set)   # (pattern, phrase) -> {question_ids}
for r in rows:
    for field in ("prompt", "option_text"):
        t = r[field]
        for name, pat in PATTERNS:
            for m in re.finditer(pat, t, flags=re.I):
                s = max(0, m.start() - 28); e = min(len(t), m.end() + 28)
                frag = ("…" if s else "") + t[s:e].strip() + ("…" if e < len(t) else "")
                hits[(name, frag)].add(r["question_id"])

md = ["""---
aliases:
tags:
  - context/personal
  - context/uade
categories:
  - "[[Task Note]]"
topics:
created: "2026-08-20 10:00"
modified:
---

# @@TITLE@@ — Accent Review

Targeted worklist for the diacritics pass on [[@@TITLE@@]].

**Do not review all @@RAW@@ `que` tokens.** Most are relative pronouns and are correct unaccented
("lo que hacés", "algo que no entendés"). Only the *interrogative / exclamative* forms take an
accent, and those appear in a small number of syntactic contexts. This file lists just those.

**How to use:** for each fragment below, decide whether the highlighted word is asking something
(→ accent it) or introducing a relative clause (→ leave it). Then apply the same decision to every
question ID listed beside it. Edit the source modules in `qbank/`, not the CSV, then re-run `build.py`.

**Separately — @@QMARK@@ prompt(s) end in `?` and need an opening `¿`:**
""" ]

for r in rows:
    p = r["prompt"]
    if p.rstrip().endswith("?"):
        md.append(f"- `{r['question_id']}` — {p}")
md.append("")

for name, _ in PATTERNS:
    group = {k: v for k, v in hits.items() if k[0] == name}
    if not group:
        continue
    md.append(f"\n## {name}  ({len(group)} fragmentos únicos)\n")
    md.append("| Fragmento | Ítems |")
    md.append("|---|---|")
    for (_, frag), qids in sorted(group.items(), key=lambda kv: -len(kv[1])):
        ids = ", ".join(sorted(qids)[:6]) + (f" +{len(qids)-6}" if len(qids) > 6 else "")
        md.append(f"| {frag.replace('|','/')} | {ids} |")

# Header placeholders are filled from THIS file, not hardcoded. The counts used
# to be the bank's (499 'que' tokens, 3 interrogative prompts) baked into the
# template, which produced confidently wrong numbers for any other source.
# Count each prompt ONCE, not once per option row — the CSV repeats the prompt
# on every option, so summing over rows triples it.
_texts = list({r["prompt"] for r in rows}) + [r["option_text"] for r in rows]
raw_que = sum(len(re.findall(r"\bque\b", t.lower())) for t in _texts)
qmark = sum(1 for p in {r["prompt"] for r in rows} if p.rstrip().endswith("?"))
title = os.path.splitext(os.path.basename(SRC))[0]
md[0] = (md[0].replace("@@TITLE@@", title)
              .replace("@@RAW@@", str(raw_que))
              .replace("@@QMARK@@", str(qmark)))

io.open(OUT, "w", encoding="utf-8").write("\n".join(md))
total = sum(len(v) for v in hits.values())
print(f"unique fragments to review: {len(hits)}")
print(f"(covering {total} token occurrences, vs {raw_que} raw 'que' hits)")
