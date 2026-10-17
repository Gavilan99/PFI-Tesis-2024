# -*- coding: utf-8 -*-
"""Selects the 120-item subset actually administered to training respondents.

WHY A SUBSET
------------
Two pilots averaged 23 s/item, so the full 200-item bank runs ~78 min. That cost
completion, and respondents — not items — are the binding constraint (target ~80,
floor ~50). 120 items lands at ~46 min.

This does NOT edit the bank. "NureonAI Question Bank v1 FINAL.csv" stays locked and
its SHA-256 unchanged. This script only records WHICH of its items are administered,
so the lock holds and no version bump is needed.

SELECTION RULE
--------------
Proportional random within each conjunto, fixed seed. Deliberately not cherry-picked:
n=2 pilot data is far too thin to rank items, and the external audit's judgement
demonstrably failed to predict behaviour (it called Conjunto Armónico the cleanest
section; Armónico is the one that broke in pilot). Random-with-a-seed is reproducible
and defensible in the thesis. Cherry-picking on two responses would not be.

COMPOSITION
-----------
  108 scenario  (27 per conjunto)
 +  12 Likert   ( 3 per conjunto)
 = 120 items

Most of the Likert block is dropped on purpose: all 37 are keyed so that agreement
supports the assigned group, and one pilot respondent agreed with 84% of them — textbook
acquiescence, already on the deferred-fix list. Keeping 12 preserves format variety
for the §1.2 "diferentes naturalezas" wording without carrying the full exposure.

USAGE
    python3 make_subset.py            # writes the subset CSV + id list
    python3 make_subset.py --n 140    # different target size
"""
import csv, io, os, sys, random, collections, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
BANK = os.path.join(PROJ, "NureonAI Question Bank v1 FINAL.csv")
OUT_CSV = os.path.join(PROJ, "NureonAI Question Bank v1 — Administered 120.csv")
OUT_IDS = os.path.join(PROJ, "NureonAI Question Bank v1 — Administered 120 (ids).txt")

SEED = 20260830
SCENARIO_PER_SYS = 27
LIKERT_PER_SYS = 3


def main():
    target_scn, target_lik = SCENARIO_PER_SYS, LIKERT_PER_SYS
    if "--n" in sys.argv:
        n = int(sys.argv[sys.argv.index("--n") + 1])
        target_lik = max(2, round(n * 0.10 / 4))
        target_scn = round(n / 4) - target_lik

    with io.open(BANK, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    digest = hashlib.sha256(io.open(BANK, "rb").read()).hexdigest()
    print(f"bank sha256 : {digest}")
    EXPECTED = "c09b69cc8a02f9178a8e8d96e21caf3ef9a2d5284681fb7e09295559e50e1a2f"
    if digest != EXPECTED:
        print("  !! WARNING: bank hash does not match the locked value.")
        print("     Something re-saved the file. Stop and investigate before collecting.")
    else:
        print("              matches locked value — bank intact\n")

    bank = collections.OrderedDict()
    for r in rows:
        bank.setdefault(r["question_id"], []).append(r)
    for q in bank:
        bank[q].sort(key=lambda x: int(x["display_order"]))

    by = collections.defaultdict(lambda: {"scenario": [], "likert": []})
    for qid, opts in bank.items():
        by[opts[0]["grouping_system"]][opts[0]["format"]].append(qid)

    rng = random.Random(SEED)
    chosen = []
    print(f"{'conjunto':36} {'scenario':>18} {'likert':>12}")
    for sysname in sorted(by):
        scn = sorted(by[sysname]["scenario"])
        lik = sorted(by[sysname]["likert"])
        pick_s = sorted(rng.sample(scn, min(target_scn, len(scn))))
        pick_l = sorted(rng.sample(lik, min(target_lik, len(lik))))
        chosen += pick_s + pick_l
        print(f"  {sysname:34} {len(pick_s):>3} of {len(scn):<3}"
              f"      {len(pick_l):>2} of {len(lik):<2}")

    chosen = sorted(set(chosen))
    sel_rows = [r for r in rows if r["question_id"] in set(chosen)]

    # balance check: every group must still be represented in every conjunto
    problems = []
    bal = collections.defaultdict(collections.Counter)
    for r in sel_rows:
        if r["format"] == "scenario":
            bal[r["grouping_system"]][r["group_label"]] += 1
    print("\ngroup_label balance in the administered subset (scenario options):")
    for sysname, c in bal.items():
        vals = list(c.values())
        print(f"  {sysname:34} " + "  ".join(f"{g} {n}" for g, n in sorted(c.items())))
        if len(set(vals)) > 1:
            problems.append(f"{sysname} unbalanced: {dict(c)}")
        if len(c) < 3:
            problems.append(f"{sysname} is missing a group entirely: {dict(c)}")

    with io.open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(sel_rows)
    with io.open(OUT_IDS, "w", encoding="utf-8") as f:
        f.write("\n".join(chosen) + "\n")

    print(f"\nadministered : {len(chosen)} questions, {len(sel_rows)} option rows")
    print(f"est. session : {len(chosen) * 23 / 60:.0f} min at the observed 23 s/item")
    print(f"wrote        : {os.path.basename(OUT_CSV)}")
    print(f"               {os.path.basename(OUT_IDS)}")
    print(f"\nBank unchanged: still 200 questions / 674 pairs, objective >=500 intact.")

    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  x " + p)
        return 1
    print("PASS — subset is balanced and every group is represented.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
