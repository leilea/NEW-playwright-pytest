from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(120))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    provider: Mapped[str] = mapped_column(String(32), default="local", server_default="local")
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    roles: Mapped[list["UserRole"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "auth"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = {"schema": "auth"}

    user_id: Mapped[int] = mapped_column(ForeignKey("auth.users.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("auth.roles.id", ondelete="CASCADE"), primary_key=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user: Mapped[User] = relationship(back_populates="roles")
    role: Mapped[Role] = relationship()


class ResourceACL(Base):
    __tablename__ = "resource_acls"
    __table_args__ = {"schema": "auth"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resource_type: Mapped[str] = mapped_column(String(32), index=True)
    resource_id: Mapped[str] = mapped_column(String(64), index=True)
    principal_type: Mapped[str] = mapped_column(String(16))
    principal_id: Mapped[str] = mapped_column(String(64), index=True)
    permission: Mapped[str] = mapped_column(String(16))
