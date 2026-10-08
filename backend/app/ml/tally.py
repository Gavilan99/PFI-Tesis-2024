"""Counting answers by `group_label`: the stub's whole method, and the input of `legacy_tree`.

Not ML. A plain count, per grouping system:

- A scenario answer adds 1 to the group of the option chosen.
- A Likert answer adds to its item's target group (every option of a Likert item carries the same
  group) according to the position chosen on the scale: (position - 1) / (options - 1). With five
  options, option 1 (minimum agreement) adds 0, option 3 adds 1/2, option 5 (maximum agreement) adds
  1. So a Likert item at full agreement weighs the same as a scenario answer, and disagreeing adds
  nothing to any group.
- The counts are normalized to a distribution per system. A system with nothing counted (no answers,
  or only Likert answers at minimum agreement) gets the uniform distribution.

Counts are exact fractions, so the same answers in any order give exactly the same distributions.
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction

from app.db.models.enums import QuestionType
from app.ml.classification import Answer
from app.ml.config import TAXONOMIES


def answer_weight(answer: Answer) -> Fraction:
    if answer.question_type is QuestionType.SCENARIO:
        return Fraction(1)
    if answer.question_type is QuestionType.MULTIPLE_CHOICE:
        if answer.option_count < 2 or not 1 <= answer.option_position <= answer.option_count:
            raise ValueError(f"Likert answer at position {answer.option_position} of {answer.option_count}")
        return Fraction(answer.option_position - 1, answer.option_count - 1)
    raise ValueError(f"question type {answer.question_type.value} is not counted")


def tally_distributions(answers: Sequence[Answer]) -> dict[str, dict[str, Fraction]]:
    counts = {system: dict.fromkeys(groups, Fraction(0)) for system, groups in TAXONOMIES.items()}
    for answer in answers:
        system_counts = counts.get(answer.grouping_system)
        if system_counts is None or answer.group_label not in system_counts:
            raise ValueError(f"group {answer.group_label!r} is not part of {answer.grouping_system!r}")
        system_counts[answer.group_label] += answer_weight(answer)

    distributions = {}
    for system, system_counts in counts.items():
        total = sum(system_counts.values())
        if total == 0:
            distributions[system] = {group: Fraction(1, len(system_counts)) for group in system_counts}
        else:
            distributions[system] = {group: count / total for group, count in system_counts.items()}
    return distributions
