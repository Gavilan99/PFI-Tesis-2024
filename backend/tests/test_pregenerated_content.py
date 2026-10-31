"""The pregenerated content (Feature 19): 27 entries (9 eneatypes x 3 account types), each one
valid under the very same length rules `app.services.personalized_descriptions` applies to a parsed
Bedrock answer (`_valid_list`/`_paragraph`), even though this content never goes through the parser.
"""

import pytest

from app.db.models.enums import AccountType
from app.services import personalized_descriptions as pd
from app.services.text_generation.pregenerated_content import PREGENERATED_CONTENT

ENEATYPES = range(1, 10)
ACCOUNT_TYPES = list(AccountType)


def test_there_are_exactly_27_entries():
    assert len(PREGENERATED_CONTENT) == 27


@pytest.mark.parametrize("eneatype", ENEATYPES)
@pytest.mark.parametrize("account_type", ACCOUNT_TYPES)
def test_every_eneatype_and_account_type_combination_exists(eneatype, account_type):
    assert (eneatype, account_type) in PREGENERATED_CONTENT


@pytest.mark.parametrize("eneatype", ENEATYPES)
@pytest.mark.parametrize("account_type", ACCOUNT_TYPES)
def test_each_entry_passes_the_same_validation_as_a_parsed_bedrock_answer(eneatype, account_type):
    content = PREGENERATED_CONTENT[(eneatype, account_type)]
    assert pd._valid_list(content["strengths"])
    assert pd._valid_list(content["tensions"])
    assert pd._paragraph([content["growth"]]) == content["growth"]
    assert pd._paragraph([content["stress"]]) == content["stress"]


def test_no_section_mentions_age_or_is_empty():
    for content in PREGENERATED_CONTENT.values():
        for section in (content["strengths"], content["tensions"]):
            assert all(line.strip() for line in section)
        assert content["growth"].strip()
        assert content["stress"].strip()
