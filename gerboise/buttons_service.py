from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from gerboise.db import Button, Message
from gerboise.schemas import ButtonIn


async def save_message_and_buttons(
    session: AsyncSession, message_id: str, channel_id: str, buttons: list[ButtonIn]
) -> None:
    session.add(Message(message_id=message_id, channel_id=channel_id))
    for button in buttons:
        session.add(
            Button(
                message_id=message_id,
                custom_id=button.custom_id,
                callback_url=button.callback_url,
            )
        )
    await session.commit()


async def get_channel_id(session: AsyncSession, message_id: str) -> str | None:
    message = await session.get(Message, message_id)
    return message.channel_id if message else None


async def replace_buttons(session: AsyncSession, message_id: str, buttons: list[ButtonIn]) -> None:
    await session.execute(delete(Button).where(Button.message_id == message_id))
    for button in buttons:
        session.add(
            Button(
                message_id=message_id,
                custom_id=button.custom_id,
                callback_url=button.callback_url,
            )
        )
    await session.commit()


async def delete_message_data(session: AsyncSession, message_id: str) -> None:
    await session.execute(delete(Button).where(Button.message_id == message_id))
    await session.execute(delete(Message).where(Message.message_id == message_id))
    await session.commit()


async def get_callback_url(session: AsyncSession, message_id: str, custom_id: str) -> str | None:
    result = await session.execute(
        select(Button.callback_url).where(
            Button.message_id == message_id, Button.custom_id == custom_id
        )
    )
    return result.scalar_one_or_none()
