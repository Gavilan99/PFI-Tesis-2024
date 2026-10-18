"""The attempt a test was continued from: `test_attempts.continued_from_attempt_id`

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-18

Feature 9 (fixed item cuts, decision of 17/10). Someone who saw their result after a cut can continue
later with the next cut without answering again. A closed attempt is never reopened and its result
is never overwritten, so the test continues in a new attempt that starts with the old one's answers
copied, linked to it here. Fourth difference with the PDR.

Nullable: an attempt that starts from scratch has no predecessor. Unique: an attempt is continued at
most once. RESTRICT, like every foreign key: no attempt the history depends on is deleted.

For the data analysis: the copied answers appear in both linked attempts. Following this link is what
keeps them from being counted twice.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("test_attempts", sa.Column("continued_from_attempt_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        op.f("fk_test_attempts_continued_from_attempt_id_test_attempts"),
        "test_attempts",
        "test_attempts",
        ["continued_from_attempt_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        op.f("uq_test_attempts_continued_from_attempt_id"), "test_attempts", ["continued_from_attempt_id"]
    )
    op.create_check_constraint(
        op.f("ck_test_attempts_not_continued_from_itself"),
        "test_attempts",
        "continued_from_attempt_id IS NULL OR continued_from_attempt_id <> id",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_test_attempts_not_continued_from_itself"), "test_attempts", type_="check")
    op.drop_constraint(op.f("uq_test_attempts_continued_from_attempt_id"), "test_attempts", type_="unique")
    op.drop_constraint(
        op.f("fk_test_attempts_continued_from_attempt_id_test_attempts"), "test_attempts", type_="foreignkey"
    )
    op.drop_column("test_attempts", "continued_from_attempt_id")
