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
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    cognito_sub: Mapped[str | None] = mapped_column(sa.String(255))
    email: Mapped[str | None] = mapped_column(sa.String(320))
    display_name: Mapped[str | None] = mapped_column(sa.String(255))
    account_type: Mapped[AccountType | None] = mapped_column(account_type_enum)
    age_range: Mapped[str | None] = mapped_column(sa.String(32))
    gender: Mapped[str | None] = mapped_column(sa.String(64))
    country: Mapped[str | None] = mapped_column(sa.String(64))
    profession_context: Mapped[str | None] = mapped_column(sa.String(255))
    is_deleted: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    created_at: Mapped[datetime] = created_now()


class Subject(Base):
    """A person tested in person by a professional account."""

    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = uuid_pk()
    professional_user_id: Mapped[uuid.UUID] = fk("users.id", nullable=False)
    label: Mapped[str | None] = mapped_column(sa.String(255))
    context_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # Reserved for the deferred delegation-link feature. Unused.
    linked_user_id: Mapped[uuid.UUID | None] = fk("users.id", nullable=True)
    created_at: Mapped[datetime] = created_now()
