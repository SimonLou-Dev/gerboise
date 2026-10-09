import logging
from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime

import discord
from discord import app_commands
from sqlalchemy.ext.asyncio import AsyncSession

from gerboise.buttons_service import get_callback_url
from gerboise.callback import relay_click
from gerboise.schemas import ButtonIn, ClickPayload, ClickUser, EmbedIn

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


def _build_embed(embed: EmbedIn | None) -> discord.Embed | None:
    if embed is None:
        return None
    discord_embed = discord.Embed(
        title=embed.title,
        description=embed.description,
        url=embed.url,
        color=embed.color,
        timestamp=embed.timestamp,
    )
    if embed.footer is not None:
        discord_embed.set_footer(text=embed.footer.text, icon_url=embed.footer.icon_url)
    if embed.author is not None:
        discord_embed.set_author(
            name=embed.author.name, url=embed.author.url, icon_url=embed.author.icon_url
        )
    if embed.image_url is not None:
        discord_embed.set_image(url=embed.image_url)
    if embed.thumbnail_url is not None:
        discord_embed.set_thumbnail(url=embed.thumbnail_url)
    for field in embed.fields:
        discord_embed.add_field(name=field.name, value=field.value, inline=field.inline)
    return discord_embed


@app_commands.command(name="status", description="Vérifie que gerboise est en ligne")
async def _status_command(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("✅ gerboise est en ligne", ephemeral=True)


class GerboiseBot(discord.Client):
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        guild_id: str | None = None,
        **kwargs: object,
    ) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents, **kwargs)
        self._session_factory = session_factory
        self._guild_id = guild_id
        self.tree = app_commands.CommandTree(self)
        self.tree.add_command(_status_command)

    async def setup_hook(self) -> None:
        if self._guild_id is not None:
            guild = discord.Object(id=int(self._guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self) -> None:
        logger.info("Logged in as %s", self.user)

    async def post_message(
        self,
        channel_id: str,
        content: str,
        embed: EmbedIn | None,
        buttons: list[ButtonIn],
    ) -> str:
        channel = await self.fetch_channel(int(channel_id))
        message = await channel.send(
            content=content, embed=_build_embed(embed), view=_build_view(buttons)
        )
        return str(message.id)

    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        content: str | None,
        embed: EmbedIn | None,
        buttons: list[ButtonIn] | None,
    ) -> None:
        channel = await self.fetch_channel(int(channel_id))
        message = await channel.fetch_message(int(message_id))
        kwargs: dict[str, object] = {}
        if content is not None:
            kwargs["content"] = content
        if embed is not None:
            kwargs["embed"] = _build_embed(embed)
        if buttons is not None:
            kwargs["view"] = _build_view(buttons)
        await message.edit(**kwargs)

    async def create_thread(
        self, channel_id: str, message_id: str, name: str, auto_archive_duration: int
    ) -> str:
        channel = await self.fetch_channel(int(channel_id))
        message = await channel.fetch_message(int(message_id))
        thread = await message.create_thread(name=name, auto_archive_duration=auto_archive_duration)
        return str(thread.id)

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
