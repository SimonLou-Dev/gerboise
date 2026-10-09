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
from gerboise.schemas import ButtonIn, MessageCreate, MessageCreated, MessagePatch
from gerboise.security import verify_api_key


class DiscordBot(Protocol):
    def is_ready(self) -> bool: ...

    async def post_message(self, channel_id: str, content: str, buttons: list[ButtonIn]) -> str: ...

    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        content: str | None,
        buttons: list[ButtonIn] | None,
    ) -> None: ...

    async def delete_message(self, channel_id: str, message_id: str) -> None: ...


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
    message_id = await bot.post_message(body.channel_id, body.content, body.buttons)
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
        channel_id, message_id, body.content, body.buttons if buttons_set else None
    )
    if buttons_set:
        await replace_buttons(session, message_id, body.buttons or [])
    return {"ok": True}


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
