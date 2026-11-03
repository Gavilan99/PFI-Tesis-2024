"""The attempt contract of the frontend, field by field: `TestAttempt`, `Question`, `AnswerOption`,
`TestResponse`, `NewResponseInput` and `CutStatus` (Feature 9).

`QuestionOut` and `AnswerOptionOut` are the instrument's exposed surface. `grouping_system`,
`group_label`, version and activity flags are not in them and must never be added: see "Lo que nunca
sale del servidor" in CLAUDE.md. Every test response is checked for them automatically.
"""

import uuid
from datetime import datetime
from typing import Annotated, Any

from pydantic import StrictBool, StringConstraints, field_validator, model_validator

from app.blueprints.schemas import ApiModel, ApiOutput
from app.db.models.enums import AttemptStatus, AttemptTier, QuestionType
from app.exceptions import TierNotAccepted


class SubjectIn(ApiModel):
    """The optional `subject` of `createTestAttempt` (Feature 20): administers the test to an
    evaluado instead of the account itself. `label` identifies them within the account (reused,
    case-insensitively, if it already names an active one); `context` precompletes the same free
    text a self-testing account would have in its profile; `consentDeclared` must be `true`, strict:
    the professional declares the informed consent anew for every test."""

    label: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
    context: Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)] | None = None
    # Defaults to false, like RegisterIn.consent_accepted: a body without it gets
    # SUBJECT_CONSENT_REQUIRED, the message that says what is missing, rather than a generic
    # validation error.
    consent_declared: StrictBool = False

    @field_validator("context")
    @classmethod
    def _blank_is_none(cls, value: str | None) -> str | None:
        return value or None


class CreateAttemptIn(ApiModel):
    """`createTestAttempt(userId)` carries nothing the server uses besides the optional `subject`.
    `userId` is tolerated and ignored (identity comes from the token); a tier is refused outright;
    anything else is unknown."""

    subject: SubjectIn | None = None

    @model_validator(mode="before")
    @classmethod
    def _refuse_tier_drop_user_id(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "tier" in data:
                raise TierNotAccepted()
            data = {key: value for key, value in data.items() if key != "userId"}
        return data


class ContinueAttemptIn(ApiModel):
    """Continuing carries nothing: no body, or an empty object. The next cut is the server's to know."""


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
    # Feature 20: the evaluado's current label (null without one, or once it was deleted) and the
    # free-text context declared for this attempt. Never the professional's own profile fields.
    subject_label: str | None
    subject_context: str | None


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


class CutStatusOut(ApiOutput):
    """`CutStatus` (cut-status.model.ts). The accuracies are the estimated eneatype accuracy of each cut,
    the number the product shows; no model version, margin or probability is part of it."""

    current_cut: int
    cut_count: int
    served_items: int
    answered_items: int
    next_cut_items: int | None
    can_continue: bool
    current_cut_accuracy: float
    next_cut_accuracy: float | None
    continued_by_attempt_id: uuid.UUID | None
