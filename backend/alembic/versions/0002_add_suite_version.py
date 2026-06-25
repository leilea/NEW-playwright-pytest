"""add suite version
Revision ID: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("suites", sa.Column("version", sa.String(32), server_default=""), schema="catalog")


def downgrade() -> None:
    op.drop_column("suites", "version", schema="catalog")
