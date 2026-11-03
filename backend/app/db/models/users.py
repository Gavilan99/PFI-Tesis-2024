import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models._columns import created_now, fk, uuid_pk
from app.db.models.enums import AccountType, account_type_enum


class User(Base):
    """An account. Never deleted physically: deletion sets `is_deleted` and anonymizes (Feature 2)."""

    __tablename__ = "users"
    __table_args__ = (
        # NULLs do not collide, so anonymized rows (cognito_sub NULL) never conflict.
        sa.UniqueConstraint("cognito_sub"),
        # Deletion anonymizes the email, so uniqueness only holds among live accounts. Case-insensitive:
        # `Juan@x.com` and `juan@x.com` are the same account.
        sa.Index(
            "uq_users_email_not_deleted",
            sa.text("lower(email)"),
            unique=True,
            postgresql_where=sa.text("NOT is_deleted"),
        ),
        # The application normalizes before writing; this makes a missed normalization fail loudly.
        sa.CheckConstraint("email = lower(email)", name="email_is_lowercase"),
        sa.CheckConstraint(
            "is_deleted = (deleted_at IS NOT NULL)", name="deleted_at_matches_flag"
        ),
        # The consent is recorded whole or not at all (NULL in both: accounts from before Feature 11).
        sa.CheckConstraint(
            "(consent_accepted_at IS NULL) = (consent_version IS NULL)", name="consent_recorded_whole"
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    cognito_sub: Mapped[str | None] = mapped_column(sa.String(255))
    email: Mapped[str | None] = mapped_column(sa.String(320))
    display_name: Mapped[str | None] = mapped_column(sa.String(255))
    # Required since Feature 20 (migration 0008): registration always sends one now. Existing rows
    # were backfilled to 'individual'.
    account_type: Mapped[AccountType] = mapped_column(account_type_enum, nullable=False)
    age_range: Mapped[str | None] = mapped_column(sa.String(32))
    gender: Mapped[str | None] = mapped_column(sa.String(64))
    country: Mapped[str | None] = mapped_column(sa.String(64))
    profession_context: Mapped[str | None] = mapped_column(sa.String(255))
    is_deleted: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    # When the person accepted the privacy policy and terms, and which version (Feature 11). Kept on
    # deletion: it is the record that the data was processed with consent.
    consent_accepted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    consent_version: Mapped[str | None] = mapped_column(sa.String(32))
    created_at: Mapped[datetime] = created_now()


class Subject(Base):
    """A person tested in person by a professional (salud/rrhh) account (Feature 20).

    `label` identifies the subject inside the professional's own account (unique, case-insensitive,
    among the active ones: the partial index below). `consent_declared_at` is the informed consent
    the professional declares when starting the subject's test; it is overwritten on every attempt,
    since the declaration is per test, not a one-time fact about the subject. `deleted_at` is this
    table's own soft delete (DELETE /api/subjects/<id>): it anonymizes `label` and `context_data`,
    like account deletion already did, and frees the label for reuse. The attempts and their results
    survive deletion, still linked by `subject_id`.
    """

    __tablename__ = "subjects"
    __table_args__ = (
        # The identifier a professional gives an evaluado does not repeat within their own active
        # ones, so reusing a label at test time reliably means "the same person". Case-insensitive,
        # and only among the active rows: a deleted one's label is free again.
        sa.Index(
            "uq_subjects_professional_user_id_label",
            "professional_user_id",
            sa.text("lower(label)"),
            unique=True,
            postgresql_where=sa.text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    professional_user_id: Mapped[uuid.UUID] = fk("users.id", nullable=False)
    label: Mapped[str | None] = mapped_column(sa.String(255))
    context_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # Reserved for the deferred delegation-link feature. Unused.
    linked_user_id: Mapped[uuid.UUID | None] = fk("users.id", nullable=True)
    consent_declared_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    created_at: Mapped[datetime] = created_now()
