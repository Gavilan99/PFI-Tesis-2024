from collections import Counter

from app.db.models.enums import GROUPS_BY_SYSTEM, GroupingSystem, QuestionType
from app.repositories import question_repository
from app.services.question_bank import load_bank, validate_bank
from scripts.seed_filler_bank import FILLER_VERSION, build_filler_bank


def test_filler_has_the_shape_of_bank_v1():
    bank = build_filler_bank()

    assert len(bank) == 200
    assert Counter(q.grouping_system for q in bank) == {system: 50 for system in GroupingSystem}
    types = Counter(q.question_type for q in bank)
    assert types == {QuestionType.SCENARIO: 163, QuestionType.MULTIPLE_CHOICE: 37}
    assert sum(len(q.options) for q in bank) == 163 * 3 + 37 * 5
    assert sorted(q.display_order for q in bank) == list(range(1, 201))
    assert validate_bank(bank) == []


def test_scenario_items_cover_their_three_groups_once_and_likert_items_share_one():
    for question in build_filler_bank():
        groups = [o.group_label for o in question.options]
        if question.question_type is QuestionType.SCENARIO:
            assert sorted(groups) == sorted(GROUPS_BY_SYSTEM[question.grouping_system])
        else:
            assert len(groups) == 5 and len(set(groups)) == 1
            assert [o.display_order for o in question.options] == [1, 2, 3, 4, 5]


def test_filler_is_deterministic_for_a_seed():
    assert build_filler_bank(7) == build_filler_bank(7)
    assert build_filler_bank(7) != build_filler_bank(8)


def test_every_text_says_it_is_filler():
    for question in build_filler_bank():
        assert question.prompt_text.startswith("[RELLENO · versión 0]")
        assert "no es un ítem del banco v1" in question.prompt_text
        assert all(o.option_text.startswith("[RELLENO]") for o in question.options)


def test_filler_text_never_names_the_answer_key():
    keys = {s.value for s in GroupingSystem} | {g for gs in GROUPS_BY_SYSTEM.values() for g in gs}
    for question in build_filler_bank():
        texts = [question.prompt_text] + [o.option_text for o in question.options]
        assert not any(key in text.lower() for key in keys for text in texts)


def test_option_position_does_not_give_away_the_group():
    first_option_groups = Counter(
        (q.grouping_system, q.options[0].group_label)
        for q in build_filler_bank()
        if q.question_type is QuestionType.SCENARIO
    )
    for system in GroupingSystem:
        seen = {group for (s, group) in first_option_groups if s is system}
        assert seen == set(GROUPS_BY_SYSTEM[system])


def test_seed_loads_as_version_zero_and_is_idempotent(db_session):
    bank = build_filler_bank()
    first = load_bank(db_session, bank, version=FILLER_VERSION, activate=True)
    second = load_bank(db_session, bank, version=FILLER_VERSION, activate=True)

    assert first.inserted == 200
    assert (second.inserted, second.unchanged) == (0, 200)
    assert question_repository.active_versions(db_session) == [0]
    assert second.counts["options"] == 674
