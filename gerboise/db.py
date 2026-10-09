from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import ForeignKey, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from gerboise.config import settings


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Message(Base):
    __tablename__ = "messages"

    message_id: Mapped[str] = mapped_column(String, primary_key=True)
    channel_id: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

    buttons: Mapped[list[Button]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )


class Button(Base):
    __tablename__ = "buttons"

    message_id: Mapped[str] = mapped_column(ForeignKey("messages.message_id"), primary_key=True)
    custom_id: Mapped[str] = mapped_column(String, primary_key=True)
    callback_url: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

    message: Mapped[Message] = relationship(back_populates="buttons")


engine = create_async_engine(f"sqlite+aiosqlite:///{settings.db_path}")
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    db_file = Path(settings.db_path)
    if db_file.parent != Path():
        db_file.parent.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session
