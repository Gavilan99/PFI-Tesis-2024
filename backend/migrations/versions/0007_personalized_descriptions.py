"""Personalized descriptions on `results`: personalized_strengths, personalized_tensions,
personalized_growth, personalized_stress, personalized_profile_hash, personalized_model and
personalized_at.

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-29

Feature 17 (descripción personalizada por Bedrock, plan pago). All nullable: most existing rows
don't have one, and an attempt that never reaches the paid tier or never has a profile never will.
The four content columns mirror the result screen's own sections (eneatype-content.ts): strengths and
tensions as short lists (JSONB), growth and stress as one paragraph each (Text).
`personalized_profile_hash` ties them to the exact profile fields and model they were generated
from; a change to either makes the next request regenerate instead of serving them stale.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "results", sa.Column("personalized_strengths", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    op.add_column(
        "results", sa.Column("personalized_tensions", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    op.add_column("results", sa.Column("personalized_growth", sa.Text(), nullable=True))
    op.add_column("results", sa.Column("personalized_stress", sa.Text(), nullable=True))
    op.add_column("results", sa.Column("personalized_profile_hash", sa.String(64), nullable=True))
    op.add_column("results", sa.Column("personalized_model", sa.String(64), nullable=True))
    op.add_column("results", sa.Column("personalized_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("results", "personalized_at")
    op.drop_column("results", "personalized_model")
    op.drop_column("results", "personalized_profile_hash")
    op.drop_column("results", "personalized_stress")
    op.drop_column("results", "personalized_growth")
    op.drop_column("results", "personalized_tensions")
    op.drop_column("results", "personalized_strengths")
