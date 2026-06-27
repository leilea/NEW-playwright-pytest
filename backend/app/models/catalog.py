from datetime import datetime
from sqlalchemy import String, Integer, Text, JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Suite(Base):
    __tablename__ = "suites"
    __table_args__ = {"schema": "catalog"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    legacy_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    version: Mapped[str] = mapped_column(String(32), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("auth.users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Case(Base):
    __tablename__ = "cases"
    __table_args__ = {"schema": "catalog"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    legacy_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    suite_id: Mapped[int] = mapped_column(ForeignKey("catalog.suites.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    version: Mapped[str] = mapped_column(String(32), default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    steps: Mapped[list] = mapped_column(JSON, default=list)
    parameters: Mapped[list] = mapped_column(JSON, default=list)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("auth.users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
