"""The order each served item's options were shown in: `responses.option_order`

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-07

Every scenario item covers its system's three groups once, so if options were always served in bank
order the position would be the group. Feature 3 shuffles them per attempt and stores the order
served, so reloading shows the same order and the dataset records what each person saw. Likert items
keep bank order: their order is the signal.

Rows that already exist get bank order. A selected option must be one of the options served.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, UUID

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("responses", sa.Column("option_order", ARRAY(UUID(as_uuid=True)), nullable=True))
    op.execute(
        """
        UPDATE responses AS r
        SET option_order = (
            SELECT array_agg(o.id ORDER BY o.display_order)
            FROM answer_options AS o
            WHERE o.question_id = r.question_id
        )
        """
    )
    op.alter_column("responses", "option_order", nullable=False)
    op.create_check_constraint(
        op.f("ck_responses_option_order_not_empty"), "responses", "cardinality(option_order) > 0"
    )
    op.create_check_constraint(
        op.f("ck_responses_selected_option_in_option_order"),
        "responses",
        "selected_option_id IS NULL OR selected_option_id = ANY (option_order)",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_responses_selected_option_in_option_order"), "responses", type_="check")
    op.drop_constraint(op.f("ck_responses_option_order_not_empty"), "responses", type_="check")
    op.drop_column("responses", "option_order")
