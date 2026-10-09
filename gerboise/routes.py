from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from gerboise.buttons_service import (
    delete_message_data,
    get_channel_id,
    replace_buttons,
    save_message_and_buttons,
)
from gerboise.db import get_session
from gerboise.schemas import (
    ButtonIn,
    EmbedIn,
    MessageCreate,
    MessageCreated,
    MessagePatch,
    ThreadCreate,
    ThreadCreated,
)
from gerboise.security import verify_api_key


class DiscordBot(Protocol):
    def is_ready(self) -> bool: ...

    async def post_message(
        self,
        channel_id: str,
        content: str,
        embed: EmbedIn | None,
        buttons: list[ButtonIn],
    ) -> str: ...

    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        content: str | None,
        embed: EmbedIn | None,
        buttons: list[ButtonIn] | None,
    ) -> None: ...

    async def delete_message(self, channel_id: str, message_id: str) -> None: ...

    async def create_thread(
        self, channel_id: str, message_id: str, name: str, auto_archive_duration: int
    ) -> str: ...


def get_bot(request: Request) -> DiscordBot:
    return request.app.state.bot


health_router = APIRouter()


@health_router.get("/healthz")
async def healthz(bot: DiscordBot = Depends(get_bot)) -> dict[str, bool]:
    return {"ok": bot.is_ready()}


messages_router = APIRouter(dependencies=[Depends(verify_api_key)])


@messages_router.post("/messages", response_model=MessageCreated)
async def create_message(
    body: MessageCreate,
    bot: DiscordBot = Depends(get_bot),
    session: AsyncSession = Depends(get_session),
) -> MessageCreated:
    message_id = await bot.post_message(body.channel_id, body.content, body.embed, body.buttons)
    await save_message_and_buttons(session, message_id, body.channel_id, body.buttons)
    return MessageCreated(message_id=message_id)


@messages_router.patch("/messages/{message_id}")
async def patch_message(
    message_id: str,
    body: MessagePatch,
    bot: DiscordBot = Depends(get_bot),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    channel_id = await get_channel_id(session, message_id)
    if channel_id is None:
        raise HTTPException(status_code=404, detail="Unknown message_id")

    buttons_set = "buttons" in body.model_fields_set
    await bot.edit_message(
        channel_id,
        message_id,
        body.content,
        body.embed,
        body.buttons if buttons_set else None,
    )
    if buttons_set:
        await replace_buttons(session, message_id, body.buttons or [])
    return {"ok": True}


@messages_router.post("/messages/{message_id}/threads", response_model=ThreadCreated)
async def create_thread(
    message_id: str,
    body: ThreadCreate,
    bot: DiscordBot = Depends(get_bot),
    session: AsyncSession = Depends(get_session),
) -> ThreadCreated:
    channel_id = await get_channel_id(session, message_id)
    if channel_id is None:
        raise HTTPException(status_code=404, detail="Unknown message_id")

    thread_id = await bot.create_thread(
        channel_id, message_id, body.name, body.auto_archive_duration
    )
    return ThreadCreated(thread_id=thread_id)


@messages_router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    bot: DiscordBot = Depends(get_bot),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    channel_id = await get_channel_id(session, message_id)
    if channel_id is not None:
        await bot.delete_message(channel_id, message_id)
    await delete_message_data(session, message_id)
    return {"ok": True}
