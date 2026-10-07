"""The guard against leaking the instrument's answer key, applied to every JSON response of the suite.

`install()` wraps Flask's test client, so every request any test makes, through any app, has its
response inspected before the test sees it. An endpoint added tomorrow is covered without anyone
having to remember it. A leak raises `AnswerKeyLeak` inside the test that made the request.

Two layers are checked here:

- Keys. No object anywhere in the payload has a key naming internal classification data, in any
  casing: the answer key (`group_label`, `grouping_system`) and the raw classifier output, which is
  stored and never exposed (`probabilities`, `predicted_group`, `confidence_margin`,
  `model_version`). A key that merely contains "confidence", "margin" or "probabilit" is refused
  too: the margin must not leave renamed or derived.
- Values. No string value is, or contains as a word, a grouping system or group label of the
  canonical vocabulary. No key is one either (`{"gut": 3}` leaks as much as `{"group": "gut"}`).
  No string names a classifier's model version.

The third layer, order, cannot be seen in a single payload; it has its own tests.
"""

import json
import re
from typing import Any

from flask.testing import FlaskClient

from app.db.models.enums import GROUP_LABELS, GroupingSystem
from app.ml.legacy.tree import LEGACY_MODEL_VERSION
from app.ml.stub import STUB_MODEL_VERSION

# Normalized: lowercase, no underscores, so group_label, groupLabel and GroupLabel are one entry.
FORBIDDEN_KEYS = frozenset(
    {
        "grouplabel",
        "groupingsystem",
        "predictedgroup",
        "confidencemargin",
        "modelversion",
        "probabilities",
    }
)
# Normalized like the above, matched anywhere inside a key: `confidenceLevel`, `margin_pct`.
FORBIDDEN_KEY_PARTS = ("confidence", "margin", "probabilit")
CANONICAL_VALUES = frozenset(GROUP_LABELS) | frozenset(system.value for system in GroupingSystem)
MODEL_VERSIONS = (STUB_MODEL_VERSION, LEGACY_MODEL_VERSION)

# A canonical value as a whole word: "gut" leaks, "gutural" does not. Underscores and hyphens belong to
# the word, so "positive_outlook" matches as one, and a base64url token (access tokens are) does not
# trip the guard by randomly containing "_gut-".
_VALUE_PATTERN = re.compile(
    r"(?<![a-z0-9_-])(?:"
    + "|".join(sorted(map(re.escape, CANONICAL_VALUES), key=len, reverse=True))
    + r")(?![a-z0-9_-])"
)


class AnswerKeyLeak(AssertionError):
    pass


class _Stats:
    json_responses = 0


stats = _Stats()


def _normalize_key(key: str) -> str:
    return key.replace("_", "").replace("-", "").lower()


def find_leaks(payload: Any, path: str = "$") -> list[str]:
    """Every leak in a decoded JSON payload, as readable locations. Empty means clean."""
    leaks: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            where = f"{path}.{key}"
            normalized = _normalize_key(str(key))
            if normalized in FORBIDDEN_KEYS or any(part in normalized for part in FORBIDDEN_KEY_PARTS):
                leaks.append(f"{where}: forbidden key")
            if _VALUE_PATTERN.search(str(key).lower()):
                leaks.append(f"{where}: key is a canonical label")
            leaks.extend(find_leaks(value, where))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            leaks.extend(find_leaks(item, f"{path}[{index}]"))
    elif isinstance(payload, str):
        match = _VALUE_PATTERN.search(payload.lower())
        if match:
            leaks.append(f"{path}: value contains canonical label '{match.group(0)}'")
        for version in MODEL_VERSIONS:
            if version in payload.lower():
                leaks.append(f"{path}: value contains model version '{version}'")
    return leaks


def check_response(response) -> None:
    """Inspect one test-client response. Non-JSON responses are not counted and not decoded."""
    if not response.is_json:
        return
    stats.json_responses += 1
    payload = json.loads(response.get_data(as_text=True) or "null")
    leaks = find_leaks(payload)
    if leaks:
        raise AnswerKeyLeak("The answer key leaked into a response:\n  " + "\n  ".join(leaks))


_installed = False


def install() -> None:
    global _installed
    if _installed:
        return
    original_open = FlaskClient.open

    def guarded_open(self, *args, **kwargs):
        response = original_open(self, *args, **kwargs)
        check_response(response)
        return response

    FlaskClient.open = guarded_open
    _installed = True
