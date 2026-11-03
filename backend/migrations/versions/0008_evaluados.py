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
an account's active subjects, case-insensitively, while freeing it once a subject is deleted. A
plain index on `test_attempts.subject_id` backs GET /api/subjects' per-subject aggregates and
DELETE /api/subjects/<id>'s `UPDATE ... WHERE subject_id = :id`, neither of which the partial
unique index (limited to `status = 'in_progress'`) helps.

Downgrade does not restore the account types or subject contexts the upgrade could not tell apart
from their defaults, and it is lossy wherever the feature was actually used: it has to discard the
subject link of every attempt (back to "every attempt is self-testing, one at a time") before the
old constraints can hold again, so it reconciles the data first — abandoning whichever extra
in-progress attempts a user accumulated one per subject, then dropping every `subject_id` — instead
of letting `ck_test_attempts_user_xor_subject` or the old unique index fail the downgrade outright.
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
    # Unlike account_type above, there is no account to backfill a subject-only attempt (allowed
    # until now by user_xor_subject) with: fail loudly and by name here rather than let it surface
    # as an opaque NOT NULL violation on the alter_column below.
    orphaned = op.get_bind().execute(sa.text("SELECT count(*) FROM test_attempts WHERE user_id IS NULL")).scalar()
    if orphaned:
        raise RuntimeError(
            f"{orphaned} test_attempts row(s) have no user_id (subject-only, allowed before this "
            "migration, never actually produced by the application). There is no account to "
            "backfill them with: resolve or remove them by hand before upgrading to 0008."
        )
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
    op.create_index("ix_test_attempts_subject_id", "test_attempts", ["subject_id"])

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
    op.drop_column("subjects", "consent_declared_at")

    # Reconcile the data the old constraints can't tell about before bringing them back: the old
    # unique index allows one in-progress attempt per user, full stop, and the old check demands
    # subject_id be NULL whenever user_id isn't — neither of which "one in progress per subject" or
    # a populated subject_id can satisfy. Both are dropped here regardless of whether the feature
    # was ever used; there is nothing to restore them from either way.
    op.drop_index("uq_test_attempts_user_subject_in_progress", table_name="test_attempts")
    op.execute(
        """
        UPDATE test_attempts SET status = 'abandoned'
        WHERE status = 'in_progress' AND id NOT IN (
            SELECT DISTINCT ON (user_id) id FROM test_attempts
            WHERE status = 'in_progress'
            ORDER BY user_id, started_at DESC
        )
        """
    )
    op.execute("UPDATE test_attempts SET subject_id = NULL WHERE subject_id IS NOT NULL")
    op.create_index(
        "uq_test_attempts_user_id_in_progress",
        "test_attempts",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'in_progress'"),
    )

    op.drop_index("ix_test_attempts_subject_id", table_name="test_attempts")
    op.drop_column("test_attempts", "subject_context")
    op.alter_column("test_attempts", "user_id", nullable=True)
    op.create_check_constraint(
        op.f("ck_test_attempts_user_xor_subject"),
        "test_attempts",
        "(user_id IS NULL) <> (subject_id IS NULL)",
    )

    op.alter_column("users", "account_type", nullable=True)
