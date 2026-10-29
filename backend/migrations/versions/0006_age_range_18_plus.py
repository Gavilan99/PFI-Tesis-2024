"""Data migration: clear `users.age_range` values NureonAI no longer accepts.

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-29

Feature 16 (NureonAI no admite menores de 18). The frontend no longer offers "Menos de 18" and the
backend now rejects any `age_range` outside the fixed list in `app.blueprints.users.schemas.AGE_RANGES`
('18-24', '25-34', '35-44', '45-54', '55-64', '65 o más'). This sets to NULL every existing row whose
age_range is 'Menos de 18' or any other value outside that list, so the column stays consistent with
the new validation going forward.

downgrade() is a no-op: the cleared values are not recoverable, there is nothing to restore them from.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ALLOWED_AGE_RANGES = ("18-24", "25-34", "35-44", "45-54", "55-64", "65 o más")


def upgrade() -> None:
    allowed = ", ".join(f"'{value}'" for value in _ALLOWED_AGE_RANGES)
    op.execute(f"UPDATE users SET age_range = NULL WHERE age_range IS NOT NULL AND age_range NOT IN ({allowed})")


def downgrade() -> None:
    """No-op: the age_range values cleared by upgrade() were not kept anywhere."""
    pass
