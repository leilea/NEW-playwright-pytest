"""add parameters to cases
Revision ID: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cases", sa.Column("parameters", sa.JSON, server_default="[]"), schema="catalog")


def downgrade() -> None:
    op.drop_column("cases", "parameters", schema="catalog")
