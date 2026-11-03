import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models._columns import created_now, fk, uuid_pk
from app.db.models.users import Subject
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
        sa.CheckConstraint(
            "(status = 'completed') = (completed_at IS NOT NULL)",
            name="completed_at_matches_status",
        ),
        # At most one attempt in progress per person: a self-testing user (subject_id NULL) or a
        # professional-administered subject (Feature 20). NULLS NOT DISTINCT (Postgres 16) makes two
        # NULL subject_ids collide, so this also still covers the self-testing case on its own.
        sa.Index(
            "uq_test_attempts_user_subject_in_progress",
            "user_id",
            "subject_id",
            unique=True,
            postgresql_where=sa.text("status = 'in_progress'"),
            postgresql_nulls_not_distinct=True,
        ),
        # Backs GET /api/subjects' per-subject aggregates and DELETE /api/subjects/<id>'s update,
        # neither of which the partial index above (limited to status = 'in_progress') helps.
        sa.Index("ix_test_attempts_subject_id", "subject_id"),
        # A closed attempt is continued at most once, in a new attempt (migration 0004).
        sa.UniqueConstraint("continued_from_attempt_id"),
        sa.CheckConstraint(
            "continued_from_attempt_id IS NULL OR continued_from_attempt_id <> id",
            name="not_continued_from_itself",
        ),
    )
    __test__ = False  # not a pytest test class, despite the name

    id: Mapped[uuid.UUID] = uuid_pk()
    # Every attempt belongs to one account (Feature 20): `user_id` is never NULL any more.
    # `subject_id` additionally names the evaluado this attempt is about, when the account
    # administered it to someone else instead of taking it themselves.
    user_id: Mapped[uuid.UUID] = fk("users.id", nullable=False)
    subject_id: Mapped[uuid.UUID | None] = fk("subjects.id", nullable=True)
    tier: Mapped[AttemptTier] = mapped_column(attempt_tier_enum, nullable=False)
    questionnaire_version: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    status: Mapped[AttemptStatus] = mapped_column(
        attempt_status_enum, nullable=False, server_default=AttemptStatus.IN_PROGRESS.value
    )
    started_at: Mapped[datetime] = created_now()
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    # The closed attempt this one continues, with its answers copied. The copies appear in both: this
    # link is what keeps an analysis from counting them twice.
    continued_from_attempt_id: Mapped[uuid.UUID | None] = fk("test_attempts.id", nullable=True)
    # The free-text context declared for this subject's test, at the time it was taken (Feature 20).
    # NULL for a self-testing attempt, or once the subject is deleted (`app.repositories.user_repository`,
    # `app.repositories.subject_repository.anonymize`). Never the subject's label.
    subject_context: Mapped[str | None] = mapped_column(sa.Text)

    subject: Mapped[Subject | None] = relationship(viewonly=True)

    @property
    def subject_label(self) -> str | None:
        """The subject's current label, or None without one or once it was anonymized. Checking
        `subject_id` first keeps a self-testing attempt (the overwhelming majority) from ever
        touching the `subject` relationship."""
        return self.subject.label if self.subject_id is not None and self.subject is not None else None


class Response(Base):
    """One row per question served to an attempt, created cut by cut.

    `selected_option_id` NULL means "asked and not answered"; no row means "not asked".
    `display_order` is the item's position inside that attempt. `option_order` is the order its options
    were served in: the bank's, for every item since Feature 9 (the order the pilot saw).
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
        sa.CheckConstraint("cardinality(option_order) > 0", name="option_order_not_empty"),
        sa.CheckConstraint(
            "selected_option_id IS NULL OR selected_option_id = ANY (option_order)",
            name="selected_option_in_option_order",
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
    option_order: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=False)
