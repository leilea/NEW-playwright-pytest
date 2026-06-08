from datetime import datetime
from sqlalchemy import String, Integer, Boolean, JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Run(Base):
    __tablename__ = "runs"
    __table_args__ = {"schema": "runtime"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    suite_id: Mapped[int | None] = mapped_column(ForeignKey("catalog.suites.id"))
    env: Mapped[str] = mapped_column(String(32))
    browser: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="queued", index=True)
    started_by: Mapped[int | None] = mapped_column(ForeignKey("auth.users.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    log_path: Mapped[str | None] = mapped_column(String(255))

class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = {"schema": "runtime"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    suite_id: Mapped[int] = mapped_column(ForeignKey("catalog.suites.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    cron: Mapped[str] = mapped_column(String(64))
    env: Mapped[str | None] = mapped_column(String(32))
    browser: Mapped[str | None] = mapped_column(String(16))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("auth.users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
