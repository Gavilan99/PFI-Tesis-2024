import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models._columns import created_now, fk, uuid_pk
from app.db.models.enums import (
    GROUP_LABELS,
    AttemptStatus,
    AttemptTier,
    GroupingSystem,
    QuestionType,
    attempt_status_enum,
    attempt_tier_enum,
    grouping_system_enum,
    question_type_enum,
)

_GROUP_LABELS_SQL = ", ".join(f"'{label}'" for label in GROUP_LABELS)


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        # A question's identity inside a version is its position in the bank. This is what makes
        # re-importing the same version idempotent.
        sa.UniqueConstraint("version", "display_order"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    grouping_system: Mapped[GroupingSystem] = mapped_column(grouping_system_enum, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(question_type_enum, nullable=False)
    prompt_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    version: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())
    display_order: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    created_at: Mapped[datetime] = created_now()

    answer_options: Mapped[list["AnswerOption"]] = relationship(
        back_populates="question", order_by="AnswerOption.display_order"
    )


class AnswerOption(Base):
    __tablename__ = "answer_options"
    __table_args__ = (
        sa.UniqueConstraint("question_id", "display_order"),
        # Target of the composite foreign key from responses: lets the database guarantee that a
        # selected option belongs to the response's question.
        sa.UniqueConstraint("question_id", "id"),
        sa.CheckConstraint(f"group_label IN ({_GROUP_LABELS_SQL})", name="group_label_canonical"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    question_id: Mapped[uuid.UUID] = fk("questions.id", nullable=False)
    option_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    group_label: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    display_order: Mapped[int] = mapped_column(sa.Integer, nullable=False)

    question: Mapped[Question] = relationship(back_populates="answer_options")


class TestAttempt(Base):
    __tablename__ = "test_attempts"
    __table_args__ = (
        # Exactly one owner: a self-testing user or a professional-administered subject.
        sa.CheckConstraint("(user_id IS NULL) <> (subject_id IS NULL)", name="user_xor_subject"),
        sa.CheckConstraint(
            "(status = 'completed') = (completed_at IS NOT NULL)",
            name="completed_at_matches_status",
        ),
        # At most one attempt in progress per user.
        sa.Index(
            "uq_test_attempts_user_id_in_progress",
            "user_id",
            unique=True,
            postgresql_where=sa.text("status = 'in_progress'"),
        ),
    )
    __test__ = False  # not a pytest test class, despite the name

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID | None] = fk("users.id", nullable=True)
    subject_id: Mapped[uuid.UUID | None] = fk("subjects.id", nullable=True)
    tier: Mapped[AttemptTier] = mapped_column(attempt_tier_enum, nullable=False)
    questionnaire_version: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    status: Mapped[AttemptStatus] = mapped_column(
        attempt_status_enum, nullable=False, server_default=AttemptStatus.IN_PROGRESS.value
    )
    started_at: Mapped[datetime] = created_now()
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class Response(Base):
    """One row per question served to an attempt, created with the attempt.

    `selected_option_id` NULL means "asked and not answered"; no row means "not asked".
    `display_order` is the item's position inside that attempt.
    """

    __tablename__ = "responses"
    __table_args__ = (
        sa.UniqueConstraint("test_attempt_id", "question_id"),
        sa.UniqueConstraint("test_attempt_id", "display_order"),
        sa.ForeignKeyConstraint(
            ["question_id", "selected_option_id"],
            ["answer_options.question_id", "answer_options.id"],
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "(selected_option_id IS NULL) = (answered_at IS NULL)",
            name="selected_option_matches_answered_at",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    test_attempt_id: Mapped[uuid.UUID] = fk("test_attempts.id", nullable=False)
    question_id: Mapped[uuid.UUID] = fk("questions.id", nullable=False)
    selected_option_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    free_text_response: Mapped[str | None] = mapped_column(sa.Text)
    ordering_response: Mapped[Any | None] = mapped_column(JSONB)
    answered_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    display_order: Mapped[int] = mapped_column(sa.Integer, nullable=False)
