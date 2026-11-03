import uuid
from datetime import datetime

from app.blueprints.schemas import ApiOutput


class SubjectOut(ApiOutput):
    """One row of GET /api/subjects (Feature 20), from `app.services.subjects.SubjectSummary`."""

    id: uuid.UUID
    label: str
    test_count: int
    last_test_at: datetime | None
    last_test_context: str | None
