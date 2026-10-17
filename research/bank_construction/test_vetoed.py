# -*- coding: utf-8 -*-
"""Expected-results test for check_vetoed.py.

Each fixture row declares what SHOULD happen:
    <rule id>  the named rule must fire
    ANY        something must fire (a known-bad string we haven't got a rule for
               yet — reported as a KNOWN GAP, not a pass)
    NONE       nothing may fire (approved v4.1 / MANTENER TAL CUAL strings)

A linter is only trustworthy if its misses are visible. Counting only the hits
would make an empty rule list look perfect.
"""
import csv, os, sys
from check_vetoed import load_rules, scan

HERE = os.path.dirname(os.path.abspath(__file__))
rules = load_rules()
fixture = list(csv.DictReader(open(os.path.join(HERE, "vetoed_fixture.csv"), encoding="utf-8")))

false_neg, wrong_rule, false_pos, gaps, ok = [], [], [], [], 0

for i, row in enumerate(fixture):
    fake = [{"option_text": row["text"], "group_label": row["group"],
             "question_id": f"F{i:03d}", "format": "scenario"}]
    fired = [h[0]["rule"] for h in scan(fake, rules)]
    exp = row["expect"]

    if exp == "NONE":
        if fired:
            false_pos.append((row, fired))
        else:
            ok += 1
    elif exp == "ANY":

        if fired:
            ok += 1
        else:
            gaps.append((row, fired))
    else:
        if not fired:
            false_neg.append((row, fired))
        elif exp not in fired:
            wrong_rule.append((row, fired))
        else:
            ok += 1

W = 74
print("=" * W)
print("VETOED-PHRASE LINTER — EXPECTED-RESULTS TEST")
print("=" * W)
print(f"fixture rows : {len(fixture)}")
print(f"rules loaded : {len(rules)}\n")


def dump(title, items, show_fired=True):
    if not items:
        return
    print(f"{title} — {len(items)}")
    for row, fired in items:
        print(f"  [{row['group']}] {row['text'][:62]}")
        print(f"      expected {row['expect']}" +
              (f"   fired {fired}" if show_fired else ""))
    print()


dump("FALSE POSITIVES (fired on an approved string)", false_pos)
dump("FALSE NEGATIVES (known-bad string, nothing fired)", false_neg)
dump("WRONG RULE (fired, but not the expected one)", wrong_rule)
dump("KNOWN GAPS (bad string, no rule written for it yet)", gaps)

print("-" * W)
print(f"passed          : {ok}/{len(fixture)}")
print(f"false positives : {len(false_pos)}   <- must be 0")
print(f"false negatives : {len(false_neg)}   <- must be 0")
print(f"wrong rule      : {len(wrong_rule)}")
print(f"known gaps      : {len(gaps)}   <- acceptable, but each is a defect the "
      f"list cannot catch")

sys.exit(1 if (false_pos or false_neg or wrong_rule) else 0)
