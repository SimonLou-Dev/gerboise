import os
import uuid
from collections.abc import AsyncIterator

os.environ.setdefault("DISCORD_BOT_TOKEN", "test-token")
os.environ.setdefault("API_KEY", "test-api-key")
os.environ.setdefault("DB_PATH", "/tmp/gerboise-test-placeholder.db")
os.environ.setdefault("LOG_LEVEL", "WARNING")

import httpx  # noqa: E402
import pytest  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from gerboise.db import Base, get_session  # noqa: E402
from gerboise.main import app  # noqa: E402
from gerboise.routes import get_bot  # noqa: E402


class FakeBot:
    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self._next_id = 1000

    def is_ready(self) -> bool:
        return True

    async def post_message(self, channel_id, content, embed, buttons):
        self._next_id += 1
        message_id = str(self._next_id)
        self.calls.append(("post", channel_id, content, embed, buttons))
        return message_id

    async def edit_message(self, channel_id, message_id, content, embed, buttons):
        self.calls.append(("edit", channel_id, message_id, content, embed, buttons))

    async def delete_message(self, channel_id, message_id):
        self.calls.append(("delete", channel_id, message_id))

    async def create_thread(self, channel_id, message_id, name, auto_archive_duration):
        self._next_id += 1
        thread_id = str(self._next_id)
        self.calls.append(("create_thread", channel_id, message_id, name, auto_archive_duration))
        return thread_id


@pytest.fixture
async def engine(tmp_path) -> AsyncIterator[object]:
    db_file = tmp_path / f"{uuid.uuid4()}.db"
    test_engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    await test_engine.dispose()


@pytest.fixture
def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
async def session(session_factory) -> AsyncIterator[AsyncSession]:
    async with session_factory() as db_session:
        yield db_session


@pytest.fixture
def fake_bot() -> FakeBot:
    return FakeBot()


@pytest.fixture
async def client(session_factory, fake_bot) -> AsyncIterator[httpx.AsyncClient]:
    async def _get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as db_session:
            yield db_session

    app.dependency_overrides[get_session] = _get_session
    app.dependency_overrides[get_bot] = lambda: fake_bot

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()
