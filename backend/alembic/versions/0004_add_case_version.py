"""add version to cases
Revision ID: 0004
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cases", sa.Column("version", sa.String(32), server_default=""), schema="catalog")


def downgrade() -> None:
    op.drop_column("cases", "version", schema="catalog")
