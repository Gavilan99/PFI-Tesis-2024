"""The consent of each account: `users.consent_accepted_at` and `users.consent_version`

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-20

Feature 11 (consent to the processing of personal data, Ley 25.326 arts. 5, 6 and 12, and decreto
1558/2001 for the transfer to the United States). Registration now requires accepting the privacy
policy and the terms; the server records when, and which version of the texts was in force
(`CONSENT_VERSION`). Fifth difference with the PDR.

Nullable: the accounts that already exist registered before there was anything to accept. Every account
created from now on has both. A CHECK keeps them together: a date without a version, or the other way
round, is not a record of anything. Deletion keeps both columns: they are the record that the data was
processed with consent.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("consent_accepted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("consent_version", sa.String(32), nullable=True))
    op.create_check_constraint(
        op.f("ck_users_consent_recorded_whole"),
        "users",
        "(consent_accepted_at IS NULL) = (consent_version IS NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_users_consent_recorded_whole"), "users", type_="check")
    op.drop_column("users", "consent_version")
    op.drop_column("users", "consent_accepted_at")
