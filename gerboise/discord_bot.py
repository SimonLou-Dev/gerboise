import logging
from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from gerboise.buttons_service import get_callback_url
from gerboise.callback import relay_click
from gerboise.schemas import ButtonIn, ClickPayload, ClickUser

logger = logging.getLogger(__name__)


def _build_view(buttons: list[ButtonIn]) -> discord.ui.View | None:
    if not buttons:
        return None
    view = discord.ui.View(timeout=None)
    for button in buttons:
        view.add_item(
            discord.ui.Button(
                label=button.label,
                custom_id=button.custom_id,
                style=discord.ButtonStyle.primary,
            )
        )
    return view


class GerboiseBot(discord.Client):
    def __init__(self, session_factory: Callable[[], AsyncSession], **kwargs: object) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents, **kwargs)
        self._session_factory = session_factory

    async def on_ready(self) -> None:
        logger.info("Logged in as %s", self.user)

    async def post_message(self, channel_id: str, content: str, buttons: list[ButtonIn]) -> str:
        channel = await self.fetch_channel(int(channel_id))
        message = await channel.send(content=content, view=_build_view(buttons))
        return str(message.id)

    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        content: str | None,
        buttons: list[ButtonIn] | None,
    ) -> None:
        channel = await self.fetch_channel(int(channel_id))
        message = await channel.fetch_message(int(message_id))
        kwargs: dict[str, object] = {}
        if content is not None:
            kwargs["content"] = content
        if buttons is not None:
            kwargs["view"] = _build_view(buttons)
        await message.edit(**kwargs)

    async def delete_message(self, channel_id: str, message_id: str) -> None:
        channel = await self.fetch_channel(int(channel_id))
        try:
            message = await channel.fetch_message(int(message_id))
        except discord.NotFound:
            return
        with suppress(discord.NotFound):
            await message.delete()

    async def on_interaction(self, interaction: discord.Interaction) -> None:
        if interaction.type is not discord.InteractionType.component:
            return
        await interaction.response.defer()

        message_id = str(interaction.message.id)
        custom_id = interaction.data.get("custom_id") if interaction.data else None
        if custom_id is None:
            return

        async with self._session_factory() as session:
            callback_url = await get_callback_url(session, message_id, custom_id)

        if callback_url is None:
            logger.warning(
                "No callback_url found for message_id=%s custom_id=%s",
                message_id,
                custom_id,
            )
            return

        payload = ClickPayload(
            message_id=message_id,
            custom_id=custom_id,
            user=ClickUser(id=str(interaction.user.id), username=interaction.user.name),
            clicked_at=datetime.now(UTC),
        )
        await relay_click(callback_url, payload)
