"""`Result` of the frontend contract (`result.model.ts`), field by field.

`confidence_margin`, the four predicted groups, their probabilities and the model version exist in
the database and are internal only (PDR): they are not in this schema and must never be added, not
as a number, not derived, not in words. Every test response is checked for them automatically.
"""

import uuid
from datetime import datetime

from app.blueprints.schemas import ApiOutput


class ResultOut(ApiOutput):
    id: uuid.UUID
    test_attempt_id: uuid.UUID
    eneatype: int
    description_text: str
    generated_at: datetime
