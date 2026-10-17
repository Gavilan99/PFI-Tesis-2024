# -*- coding: utf-8 -*-
"""Cross-system wording-collision check for the NureonAI question bank.

WHY THIS EXISTS
---------------
The four classifiers are only useful if their errors are roughly independent.
If the SAME phrase is keyed to two different grouping systems, the same surface
trait supplies "evidence" to two supposedly independent classifiers, and their
errors become correlated — which quietly defeats the error-correcting property
the whole 4-classifier architecture rests on.

This is the one defect class that per-item SHAP CANNOT surface: SHAP will simply
report both items as important and the correlation stays invisible.

Run this after ANY item edit — not just on the item you touched. During the v1.2
pass, one fix silently created a brand-new collision (Q069 vs Q118) that was only
caught because the full scan was re-run.

USAGE
-----
    python3 check_overlap.py                # scans the default bank CSV
    python3 check_overlap.py --threshold .4 # stricter
    python3 check_overlap.py path/to.csv

Exit code 1 if any collision is at or above threshold, so it can gate a commit.
"""
import csv, re, sys, os, itertools

DEFAULT_CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "NureonAI Question Bank v1.2.csv")

# Function words carry no construct meaning; ignoring them stops trivially
# similar short options from looking like collisions.
STOP = set("""que de la el los las un una y o a en se te lo le su tu vos no es mas más por
para con del al sin ya si como cuando lo mi me nos ese esa eso este esta esto muy tan
ser estar hacer tener""".split())


def content_words(text):
    return {w for w in re.findall(r"[a-záéíóúñ]+", text.lower())
            if w not in STOP and len(w) > 3}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if args else DEFAULT_CSV
    thr = 0.45
    for a in sys.argv[1:]:
        if a.startswith("--threshold"):
            thr = float(a.split("=", 1)[1]) if "=" in a else 0.45

    with open(path, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["format"] == "scenario"]

    print(f"bank      : {os.path.basename(path)}")
    print(f"options   : {len(rows)} scenario rows")
    print(f"threshold : Jaccard >= {thr} on content words, cross-system only\n")

    hits = []
    for x, y in itertools.combinations(rows, 2):
        if x["grouping_system"] == y["grouping_system"]:
            continue                      # within-system overlap is expected
        sx, sy = content_words(x["option_text"]), content_words(y["option_text"])
        if len(sx) < 2 or len(sy) < 2:
            continue                      # too short to judge
        j = jaccard(sx, sy)
        if j >= thr:
            hits.append((j, x, y))

    for j, x, y in sorted(hits, key=lambda h: -h[0]):
        print(f"  {j:.2f}  {x['question_id']} [{x['group_label']}] {x['option_text']!r}")
        print(f"        {y['question_id']} [{y['group_label']}] {y['option_text']!r}")
        print(f"        shared: {', '.join(sorted(content_words(x['option_text']) & content_words(y['option_text'])))}\n")

    if hits:
        print(f"FAIL — {len(hits)} cross-system collision(s) at or above {thr}.")
        print("Reword one side of each pair, re-run build.py, then re-run this check.")
        return 1
    print("PASS — no cross-system wording collisions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
