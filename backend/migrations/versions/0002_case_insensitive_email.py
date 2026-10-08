"""Case-insensitive email: `Juan@x.com` and `juan@x.com` are the same account

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-06

Feature 1 left the live-email unique index case-sensitive on purpose, to be settled here. Emails are
lowercased, the index compares `lower(email)`, and a CHECK keeps them stored lowercase. Two live
accounts that differ only in case would make the upgrade fail on the new index, by design: that is
a duplicate a person has to resolve, not something to merge silently.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE users SET email = lower(email) WHERE email <> lower(email)")
    op.drop_index("uq_users_email_not_deleted", table_name="users")
    op.create_index(
        "uq_users_email_not_deleted",
        "users",
        [sa.text("lower(email)")],
        unique=True,
        postgresql_where=sa.text("NOT is_deleted"),
    )
    op.create_check_constraint(op.f("ck_users_email_is_lowercase"), "users", "email = lower(email)")


def downgrade() -> None:
    op.drop_constraint(op.f("ck_users_email_is_lowercase"), "users", type_="check")
    op.drop_index("uq_users_email_not_deleted", table_name="users")
    op.create_index(
        "uq_users_email_not_deleted",
        "users",
        ["email"],
        unique=True,
        postgresql_where=sa.text("NOT is_deleted"),
    )
