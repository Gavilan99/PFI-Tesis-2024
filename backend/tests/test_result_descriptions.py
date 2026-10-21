"""The result's description is the frontend's `summary` of the same eneatype, word for word.

The text is written in the frontend (`eneatype-content.ts`) and copied into
`app/services/result_descriptions.py`; this reads the frontend file so the copy can't drift.
"""

import re
from pathlib import Path

from app.services.result_descriptions import DESCRIPTIONS

CONTENT = (
    Path(__file__).resolve().parents[2]
    / "frontend" / "nureon" / "src" / "app" / "resultados" / "eneatype-content.ts"
)
# `  4: {` then, a few lines below, `summary: '...'`, inside ENEATYPE_CONTENT.
_SUMMARY = re.compile(r"^\s*([1-9]): \{\s*title: '[^']*',\s*summary: '([^']*)',", re.MULTILINE)


def _frontend_summaries() -> dict[int, str]:
    return {int(number): text for number, text in _SUMMARY.findall(CONTENT.read_text(encoding="utf-8"))}


def test_every_eneatype_has_a_description():
    assert set(DESCRIPTIONS) == set(range(1, 10))
    assert all(text.strip() for text in DESCRIPTIONS.values())


def test_the_descriptions_match_the_frontend_summaries():
    assert _frontend_summaries() == DESCRIPTIONS
