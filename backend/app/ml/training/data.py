"""Pilot data: who answered what, and their expert type. Private data, read from outside the repo.

- responses: the wide CSV written by `research/pilot/parse_form_export.py`, one row per respondent,
  `respondent_id` plus one column per item code with the chosen position (1-based).
- labels: a CSV with `codigo` and `tipo_asignado` (1-9), the expert typing. Each respondent's group
  in each system is derived from the type through the canonical table, never from the options.
- exclusions (optional): a text file with one respondent code per line (`#` starts a comment).

Only respondents present in both files, with a type, and not excluded are used.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from app.ml.config import TYPE_TABLE
from app.ml.training.bank import Item

NOT_ASKED = "NO_PREGUNTADO"


@dataclass(frozen=True)
class Sample:
    codes: list[str]                      # respondent codes, in file order
    answers: list[dict[str, int]]         # per respondent: {item code: position}
    types: list[int]                      # expert type, 1-9
    groups: dict[str, list[str]]          # per system: the respondent's group, aligned with codes


def read_list(path: str | Path | None) -> set[str]:
    if not path:
        return set()
    out = set()
    for line in open(path, encoding="utf-8"):
        code = line.split("#")[0].strip()
        if code:
            out.add(code)
    return out


def load_sample(responses: str | Path, labels: str | Path, items: list[Item],
                exclude: set[str] | None = None) -> Sample:
    exclude = exclude or set()
    with open(labels, encoding="utf-8-sig", newline="") as fh:
        types = {}
        for row in csv.DictReader(fh):
            t = (row.get("tipo_asignado") or "").strip()
            if t:
                types[row["codigo"].strip()] = int(float(t))
    codes, answers, tlist = [], [], []
    with open(responses, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            code = row["respondent_id"].strip()
            if code in exclude or code not in types:
                continue
            ans = {}
            for it in items:
                v = (row.get(it.code) or "").strip()
                if v and v != NOT_ASKED:
                    ans[it.code] = int(v)
            missing = [it.code for it in items if it.code not in ans]
            if missing:
                raise ValueError(f"a respondent has {len(missing)} unanswered items; the pilot "
                                 "answered the full bank, so this is a data error")
            codes.append(code); answers.append(ans); tlist.append(types[code])
    for t in tlist:
        if t not in TYPE_TABLE:
            raise ValueError(f"type {t} is not 1-9")
    systems = list(next(iter(TYPE_TABLE.values())))
    groups = {s: [TYPE_TABLE[t][s] for t in tlist] for s in systems}
    return Sample(codes=codes, answers=answers, types=tlist, groups=groups)
