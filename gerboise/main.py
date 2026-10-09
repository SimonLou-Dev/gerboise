import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from gerboise.config import settings
from gerboise.db import AsyncSessionLocal, engine, init_db
from gerboise.discord_bot import GerboiseBot
from gerboise.routes import health_router, messages_router


def configure_logging() -> None:
    logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await init_db()

    bot = GerboiseBot(session_factory=AsyncSessionLocal, guild_id=settings.discord_guild_id)
    task = asyncio.create_task(bot.start(settings.discord_bot_token.get_secret_value()))
    app.state.bot = bot

    try:
        yield
    finally:
        await bot.close()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        await engine.dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(health_router)
app.include_router(messages_router)
