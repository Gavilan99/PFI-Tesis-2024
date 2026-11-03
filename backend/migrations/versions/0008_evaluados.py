"""Evaluados: subjects tested in person from a salud/rrhh account (Feature 20).

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-02

`users.account_type` is now required: existing NULL rows are backfilled to 'individual' (the
default a self-testing account would have chosen) and the column becomes NOT NULL.

`test_attempts` drops `user_xor_subject`: every attempt now belongs to one account (`user_id`,
NOT NULL from here on), optionally naming the evaluado it was administered to (`subject_id`,
unchanged). The in-progress limit of one attempt at a time moves from "per user" to "per person"
(user, and subject when there is one): the old partial unique index on `user_id` is replaced by one
on `(user_id, subject_id)`, NULLS NOT DISTINCT (Postgres 16) so two self-testing attempts (both
NULL) still collide exactly as before. `subject_context` is the free-text context declared for a
subject's test, independent from the subject's own stored data.

`subjects` gets `consent_declared_at` (the informed consent declared at test time; existing rows,
all unused so far, are backfilled to their `created_at`) and `deleted_at` (this table's own soft
delete, `DELETE /api/subjects/<id>`). The partial unique index keeps a label from repeating within
an account's active subjects, case-insensitively, while freeing it once a subject is deleted.

Downgrade does not restore the account types or subject contexts the upgrade could not tell apart
from their defaults; nothing else here is lossy.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users.account_type ------------------------------------------------------------------
    op.execute("UPDATE users SET account_type = 'individual' WHERE account_type IS NULL")
    op.alter_column("users", "account_type", nullable=False)

    # --- test_attempts ------------------------------------------------------------------------
    op.drop_constraint(op.f("ck_test_attempts_user_xor_subject"), "test_attempts", type_="check")
    op.alter_column("test_attempts", "user_id", nullable=False)
    op.add_column("test_attempts", sa.Column("subject_context", sa.Text(), nullable=True))
    op.drop_index("uq_test_attempts_user_id_in_progress", table_name="test_attempts")
    op.create_index(
        "uq_test_attempts_user_subject_in_progress",
        "test_attempts",
        ["user_id", "subject_id"],
        unique=True,
        postgresql_where=sa.text("status = 'in_progress'"),
        postgresql_nulls_not_distinct=True,
    )

    # --- subjects -----------------------------------------------------------------------------
    op.add_column("subjects", sa.Column("consent_declared_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE subjects SET consent_declared_at = created_at WHERE consent_declared_at IS NULL")
    op.alter_column("subjects", "consent_declared_at", nullable=False)
    op.add_column("subjects", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "uq_subjects_professional_user_id_label",
        "subjects",
        ["professional_user_id", sa.text("lower(label)")],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_subjects_professional_user_id_label", table_name="subjects")
    op.drop_column("subjects", "deleted_at")
    op.alter_column("subjects", "consent_declared_at", nullable=True)
    op.drop_column("subjects", "consent_declared_at")

    op.drop_index("uq_test_attempts_user_subject_in_progress", table_name="test_attempts")
    op.create_index(
        "uq_test_attempts_user_id_in_progress",
        "test_attempts",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'in_progress'"),
    )
    op.drop_column("test_attempts", "subject_context")
    op.alter_column("test_attempts", "user_id", nullable=True)
    op.create_check_constraint(
        op.f("ck_test_attempts_user_xor_subject"),
        "test_attempts",
        "(user_id IS NULL) <> (subject_id IS NULL)",
    )

    op.alter_column("users", "account_type", nullable=True)
