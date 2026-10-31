"""`Result` of the frontend contract (`result.model.ts`), field by field.

`confidence_margin`, the four predicted groups, their probabilities and the model version exist in
the database and are internal only (PDR): they are not in this schema and must never be added, not
as a number, not derived, not in words. Every test response is checked for them automatically.
"""

import uuid
from datetime import datetime
from typing import Literal

from app.blueprints.schemas import ApiOutput


class ResultOut(ApiOutput):
    id: uuid.UUID
    test_attempt_id: uuid.UUID
    eneatype: int
    description_text: str
    generated_at: datetime


class PersonalizedDescriptionOut(ApiOutput):
    """`PersonalizedDescription` of result.model.ts (Feature 17): a personalized version of the
    result screen's own four sections (eneatype-content.ts). All four are null for every status but
    "personalized"."""

    status: Literal["not_in_plan", "profile_missing", "personalized", "unavailable"]
    strengths: list[str] | None
    tensions: list[str] | None
    growth: str | None
    stress: str | None
