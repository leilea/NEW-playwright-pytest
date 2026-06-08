"""init auth/catalog/runtime/audit
Revision ID: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")
    op.execute("CREATE SCHEMA IF NOT EXISTS catalog")
    op.execute("CREATE SCHEMA IF NOT EXISTS runtime")
    op.execute("CREATE SCHEMA IF NOT EXISTS audit")
    op.create_table(
        "users", sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("display_name", sa.String(120)),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("provider", sa.String(32), nullable=False, server_default="local"),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="auth",
    )
    op.create_index("ix_users_external_id", "users", ["external_id"], schema="auth")
    op.create_table(
        "roles", sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(32), unique=True, nullable=False),
        schema="auth",
    )
    op.create_table(
        "user_roles", sa.Column("user_id", sa.Integer, sa.ForeignKey("auth.users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("auth.roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="auth",
    )
    op.create_table(
        "resource_acls",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("resource_type", sa.String(32), nullable=False, index=True),
        sa.Column("resource_id", sa.String(64), nullable=False, index=True),
        sa.Column("principal_type", sa.String(16), nullable=False),
        sa.Column("principal_id", sa.String(64), nullable=False, index=True),
        sa.Column("permission", sa.String(16), nullable=False),
        sa.UniqueConstraint("resource_type", "resource_id", "principal_type", "principal_id", "permission"),
        schema="auth",
    )
    op.create_table(
        "suites", sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, index=True),
        sa.Column("description", sa.Text, server_default=""),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("auth.users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="catalog",
    )
    op.create_table(
        "cases", sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("suite_id", sa.Integer, sa.ForeignKey("catalog.suites.id", ondelete="CASCADE"), index=True),
        sa.Column("name", sa.String(160), nullable=False, index=True),
        sa.Column("tags", sa.JSON, server_default="[]"),
        sa.Column("steps", sa.JSON, server_default="[]"),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("auth.users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="catalog",
    )
    op.create_table(
        "runs", sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("suite_id", sa.Integer, sa.ForeignKey("catalog.suites.id")),
        sa.Column("env", sa.String(32), nullable=False),
        sa.Column("browser", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="queued", index=True),
        sa.Column("started_by", sa.Integer, sa.ForeignKey("auth.users.id")),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", sa.JSON, server_default="{}"),
        sa.Column("log_path", sa.String(255)),
        schema="runtime",
    )
    op.create_table(
        "schedules", sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("suite_id", sa.Integer, sa.ForeignKey("catalog.suites.id", ondelete="CASCADE")),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("cron", sa.String(64), nullable=False),
        sa.Column("env", sa.String(32)),
        sa.Column("browser", sa.String(16)),
        sa.Column("enabled", sa.Boolean, server_default=sa.text("true")),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("auth.users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="runtime",
    )
    op.create_table(
        "audit_events", sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("auth.users.id")),
        sa.Column("action", sa.String(64), nullable=False, index=True),
        sa.Column("target_type", sa.String(32)),
        sa.Column("target_id", sa.String(64)),
        sa.Column("payload", sa.JSON, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        schema="audit",
    )

def downgrade() -> None:
    op.drop_table("audit_events", schema="audit")
    op.drop_table("schedules", schema="runtime")
    op.drop_table("runs", schema="runtime")
    op.drop_table("cases", schema="catalog")
    op.drop_table("suites", schema="catalog")
    op.drop_table("resource_acls", schema="auth")
    op.drop_table("user_roles", schema="auth")
    op.drop_table("roles", schema="auth")
    op.drop_table("users", schema="auth")
    op.execute("DROP SCHEMA IF EXISTS audit")
    op.execute("DROP SCHEMA IF EXISTS runtime")
    op.execute("DROP SCHEMA IF EXISTS catalog")
    op.execute("DROP SCHEMA IF EXISTS auth")
