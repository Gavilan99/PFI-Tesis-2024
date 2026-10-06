import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models._columns import created_now, fk, uuid_pk
from app.db.models.enums import GroupingSystem, grouping_system_enum


class ClassifierPrediction(Base):
    """Raw output of one classifier for one attempt. Internal only: never leaves the server."""

    __tablename__ = "classifier_predictions"
    __table_args__ = (sa.UniqueConstraint("test_attempt_id", "grouping_system"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    test_attempt_id: Mapped[uuid.UUID] = fk("test_attempts.id", nullable=False)
    grouping_system: Mapped[GroupingSystem] = mapped_column(grouping_system_enum, nullable=False)
    predicted_group: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    probabilities: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    model_version: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    created_at: Mapped[datetime] = created_now()


class Result(Base):
    __tablename__ = "results"
    __table_args__ = (
        sa.UniqueConstraint("test_attempt_id"),
        sa.CheckConstraint("eneatype BETWEEN 1 AND 9", name="eneatype_range"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    test_attempt_id: Mapped[uuid.UUID] = fk("test_attempts.id", nullable=False)
    eneatype: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    # Internal only.
    confidence_margin: Mapped[Decimal | None] = mapped_column(sa.Numeric)
    description_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    generated_at: Mapped[datetime] = created_now()


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (sa.CheckConstraint("rating BETWEEN 1 AND 5", name="rating_range"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    test_attempt_id: Mapped[uuid.UUID | None] = fk("test_attempts.id", nullable=True)
    user_id: Mapped[uuid.UUID | None] = fk("users.id", nullable=True)
    rating: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(sa.Text)
    submitted_at: Mapped[datetime] = created_now()
