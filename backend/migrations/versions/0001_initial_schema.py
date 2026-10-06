"""Initial schema: the 11 tables of the data-model PDR

Revision ID: 0001
Revises:
Create Date: 2026-10-06

Two differences with the PDR, decided on 05-10: `responses.answered_at` is nullable and
`responses.display_order` exists, because the subset served to an attempt is stored as
pre-created `responses` rows.

Every foreign key is ON DELETE RESTRICT: the full history is preserved and no cascade deletes
responses. Values are frozen here on purpose; this file does not import the application.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ENUMS = {
    "account_type": ("individual", "rrhh", "salud"),
    "grouping_system": ("intelligence_centers", "hornevian", "harmonic", "object_relations"),
    "question_type": ("multiple_choice", "ordering", "text", "scenario"),
    "attempt_tier": ("free_reduced", "paid_full"),
    "attempt_status": ("in_progress", "completed", "abandoned"),
    "subscription_tier": ("individual", "basic", "intermediate", "pro", "unlimited"),
    "subscription_status": ("active", "cancelled", "past_due", "trialing"),
}

GROUP_LABELS = (
    "gut", "heart", "head",
    "assertive", "compliant", "withdrawn",
    "positive_outlook", "competency", "reactive",
    "attachment", "frustration", "rejection",
)


def _enum(name: str) -> postgresql.ENUM:
    return postgresql.ENUM(*ENUMS[name], name=name, create_type=False)


def _id() -> sa.Column:
    return sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False)


def _now(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False)


def _fk(columns: list[str], refcolumns: list[str], name: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(columns, refcolumns, name=op.f(name), ondelete="RESTRICT")


def upgrade() -> None:
    bind = op.get_bind()
    for name, values in ENUMS.items():
        postgresql.ENUM(*values, name=name).create(bind, checkfirst=False)

    op.create_table(
        "users",
        _id(),
        sa.Column("cognito_sub", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("account_type", _enum("account_type"), nullable=True),
        sa.Column("age_range", sa.String(length=32), nullable=True),
        sa.Column("gender", sa.String(length=64), nullable=True),
        sa.Column("country", sa.String(length=64), nullable=True),
        sa.Column("profession_context", sa.String(length=255), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        _now("created_at"),
        sa.CheckConstraint(
            "is_deleted = (deleted_at IS NOT NULL)", name=op.f("ck_users_deleted_at_matches_flag")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("cognito_sub", name=op.f("uq_users_cognito_sub")),
    )
    # Deletion anonymizes the email, so uniqueness only holds among live accounts.
    op.create_index(
        "uq_users_email_not_deleted",
        "users",
        ["email"],
        unique=True,
        postgresql_where=sa.text("NOT is_deleted"),
    )

    op.create_table(
        "subjects",
        _id(),
        sa.Column("professional_user_id", sa.UUID(), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("context_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("linked_user_id", sa.UUID(), nullable=True),
        _now("created_at"),
        _fk(["professional_user_id"], ["users.id"], "fk_subjects_professional_user_id_users"),
        _fk(["linked_user_id"], ["users.id"], "fk_subjects_linked_user_id_users"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subjects")),
    )

    op.create_table(
        "questions",
        _id(),
        sa.Column("grouping_system", _enum("grouping_system"), nullable=False),
        sa.Column("question_type", _enum("question_type"), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        _now("created_at"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_questions")),
        sa.UniqueConstraint(
            "version", "display_order", name=op.f("uq_questions_version_display_order")
        ),
    )

    op.create_table(
        "answer_options",
        _id(),
        sa.Column("question_id", sa.UUID(), nullable=False),
        sa.Column("option_text", sa.Text(), nullable=False),
        sa.Column("group_label", sa.String(length=32), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "group_label IN (" + ", ".join(f"'{g}'" for g in GROUP_LABELS) + ")",
            name=op.f("ck_answer_options_group_label_canonical"),
        ),
        _fk(["question_id"], ["questions.id"], "fk_answer_options_question_id_questions"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_answer_options")),
        sa.UniqueConstraint(
            "question_id", "display_order", name=op.f("uq_answer_options_question_id_display_order")
        ),
        # Target of the composite foreign key from responses.
        sa.UniqueConstraint("question_id", "id", name=op.f("uq_answer_options_question_id_id")),
    )

    op.create_table(
        "test_attempts",
        _id(),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("subject_id", sa.UUID(), nullable=True),
        sa.Column("tier", _enum("attempt_tier"), nullable=False),
        sa.Column("questionnaire_version", sa.Integer(), nullable=False),
        sa.Column(
            "status", _enum("attempt_status"), server_default="in_progress", nullable=False
        ),
        _now("started_at"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(user_id IS NULL) <> (subject_id IS NULL)", name=op.f("ck_test_attempts_user_xor_subject")
        ),
        sa.CheckConstraint(
            "(status = 'completed') = (completed_at IS NOT NULL)",
            name=op.f("ck_test_attempts_completed_at_matches_status"),
        ),
        _fk(["user_id"], ["users.id"], "fk_test_attempts_user_id_users"),
        _fk(["subject_id"], ["subjects.id"], "fk_test_attempts_subject_id_subjects"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_attempts")),
    )
    op.create_index(
        "uq_test_attempts_user_id_in_progress",
        "test_attempts",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'in_progress'"),
    )

    op.create_table(
        "responses",
        _id(),
        sa.Column("test_attempt_id", sa.UUID(), nullable=False),
        sa.Column("question_id", sa.UUID(), nullable=False),
        sa.Column("selected_option_id", sa.UUID(), nullable=True),
        sa.Column("free_text_response", sa.Text(), nullable=True),
        sa.Column("ordering_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "(selected_option_id IS NULL) = (answered_at IS NULL)",
            name=op.f("ck_responses_selected_option_matches_answered_at"),
        ),
        _fk(["test_attempt_id"], ["test_attempts.id"], "fk_responses_test_attempt_id_test_attempts"),
        _fk(["question_id"], ["questions.id"], "fk_responses_question_id_questions"),
        # The selected option must belong to this response's question.
        _fk(
            ["question_id", "selected_option_id"],
            ["answer_options.question_id", "answer_options.id"],
            "fk_responses_question_id_selected_option_id_answer_options",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_responses")),
        sa.UniqueConstraint(
            "test_attempt_id", "question_id", name=op.f("uq_responses_test_attempt_id_question_id")
        ),
        sa.UniqueConstraint(
            "test_attempt_id", "display_order", name=op.f("uq_responses_test_attempt_id_display_order")
        ),
    )

    op.create_table(
        "classifier_predictions",
        _id(),
        sa.Column("test_attempt_id", sa.UUID(), nullable=False),
        sa.Column("grouping_system", _enum("grouping_system"), nullable=False),
        sa.Column("predicted_group", sa.String(length=32), nullable=False),
        sa.Column("probabilities", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        _now("created_at"),
        _fk(
            ["test_attempt_id"],
            ["test_attempts.id"],
            "fk_classifier_predictions_test_attempt_id_test_attempts",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_classifier_predictions")),
        sa.UniqueConstraint(
            "test_attempt_id",
            "grouping_system",
            name=op.f("uq_classifier_predictions_test_attempt_id_grouping_system"),
        ),
    )

    op.create_table(
        "results",
        _id(),
        sa.Column("test_attempt_id", sa.UUID(), nullable=False),
        sa.Column("eneatype", sa.Integer(), nullable=False),
        sa.Column("confidence_margin", sa.Numeric(), nullable=True),
        sa.Column("description_text", sa.Text(), nullable=False),
        _now("generated_at"),
        sa.CheckConstraint("eneatype BETWEEN 1 AND 9", name=op.f("ck_results_eneatype_range")),
        _fk(["test_attempt_id"], ["test_attempts.id"], "fk_results_test_attempt_id_test_attempts"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_results")),
        sa.UniqueConstraint("test_attempt_id", name=op.f("uq_results_test_attempt_id")),
    )

    op.create_table(
        "feedback",
        _id(),
        sa.Column("test_attempt_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        _now("submitted_at"),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name=op.f("ck_feedback_rating_range")),
        _fk(["test_attempt_id"], ["test_attempts.id"], "fk_feedback_test_attempt_id_test_attempts"),
        _fk(["user_id"], ["users.id"], "fk_feedback_user_id_users"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_feedback")),
    )

    op.create_table(
        "subscriptions",
        _id(),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("tier", _enum("subscription_tier"), nullable=False),
        sa.Column("status", _enum("subscription_status"), nullable=False),
        sa.Column("mercadopago_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        _now("created_at"),
        _now("updated_at"),
        _fk(["user_id"], ["users.id"], "fk_subscriptions_user_id_users"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subscriptions")),
    )

    op.create_table(
        "payments",
        _id(),
        sa.Column("subscription_id", sa.UUID(), nullable=False),
        sa.Column("mercadopago_payment_id", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        _fk(["subscription_id"], ["subscriptions.id"], "fk_payments_subscription_id_subscriptions"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payments")),
        # What makes the Mercado Pago webhook idempotent.
        sa.UniqueConstraint(
            "mercadopago_payment_id", name=op.f("uq_payments_mercadopago_payment_id")
        ),
    )


def downgrade() -> None:
    for table in (
        "payments",
        "subscriptions",
        "feedback",
        "results",
        "classifier_predictions",
        "responses",
        "test_attempts",
        "answer_options",
        "questions",
        "subjects",
        "users",
    ):
        op.drop_table(table)

    bind = op.get_bind()
    for name in reversed(ENUMS):
        postgresql.ENUM(name=name).drop(bind, checkfirst=False)
