"""add_product_check_constraints

Revision ID: d65286cede13
Revises: d3735d93c1c5
Create Date: 2026-09-14 14:26:18.226783

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd65286cede13'
down_revision: Union[str, Sequence[str], None] = 'd3735d93c1c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "check_product_stock_quantity_non_negative",
        "products",
        "stock_quantity >= 0",
    )
    op.create_check_constraint(
        "check_product_price_positive",
        "products",
        "price > 0",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("check_product_stock_quantity_non_negative", "products", type_="check")
    op.drop_constraint("check_product_price_positive", "products", type_="check")
