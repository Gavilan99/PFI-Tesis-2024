"""The attempt contract of the frontend, field by field: `TestAttempt`, `Question`, `AnswerOption`,
`TestResponse` and `NewResponseInput`.

`QuestionOut` and `AnswerOptionOut` are the instrument's exposed surface. `grouping_system`,
`group_label`, version and activity flags are not in them and must never be added: see "Lo que nunca
sale del servidor" in CLAUDE.md. Every test response is checked for them automatically.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import model_validator

from app.blueprints.schemas import ApiModel, ApiOutput
from app.db.models.enums import AttemptStatus, AttemptTier, QuestionType
from app.exceptions import TierNotAccepted


class CreateAttemptIn(ApiModel):
    """`createTestAttempt(userId)` carries nothing the server uses. `userId` is tolerated and ignored
    (identity comes from the token); a tier is refused outright; anything else is unknown."""

    @model_validator(mode="before")
    @classmethod
    def _refuse_tier_drop_user_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "tier" in data:
                raise TierNotAccepted()
            data = {key: value for key, value in data.items() if key != "userId"}
        return data


class NewResponseIn(ApiModel):
    """`NewResponseInput`, exactly. Free text and ordering items are out of scope: both must be null."""

    question_id: uuid.UUID
    selected_option_id: uuid.UUID
    free_text_response: None
    ordering_response: None


class TestAttemptOut(ApiOutput):
    __test__ = False  # not a pytest test class, despite the name

    id: uuid.UUID
    user_id: uuid.UUID | None
    subject_id: uuid.UUID | None
    tier: AttemptTier
    questionnaire_version: int
    status: AttemptStatus
    started_at: datetime
    completed_at: datetime | None


class AnswerOptionOut(ApiOutput):
    id: uuid.UUID
    question_id: uuid.UUID
    option_text: str
    display_order: int


class QuestionOut(ApiOutput):
    id: uuid.UUID
    question_type: QuestionType
    prompt_text: str
    display_order: int
    answer_options: list[AnswerOptionOut]


class TestResponseOut(ApiOutput):
    __test__ = False

    id: uuid.UUID
    test_attempt_id: uuid.UUID
    question_id: uuid.UUID
    selected_option_id: uuid.UUID | None
    free_text_response: str | None
    ordering_response: Any | None
    answered_at: datetime
