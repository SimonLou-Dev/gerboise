from gerboise.buttons_service import (
    delete_message_data,
    get_callback_url,
    get_channel_id,
    replace_buttons,
    save_message_and_buttons,
)
from gerboise.schemas import ButtonIn


async def test_save_message_without_buttons(session):
    await save_message_and_buttons(session, "1", "100", [])

    assert await get_channel_id(session, "1") == "100"
    assert await get_callback_url(session, "1", "anything") is None


async def test_save_message_with_buttons(session):
    buttons = [ButtonIn(label="Go", custom_id="go", callback_url="https://example.com/cb")]

    await save_message_and_buttons(session, "2", "100", buttons)

    assert await get_callback_url(session, "2", "go") == "https://example.com/cb"


async def test_replace_buttons_removes_old_ones(session):
    await save_message_and_buttons(
        session,
        "3",
        "100",
        [ButtonIn(label="Go", custom_id="go", callback_url="https://example.com/cb")],
    )

    await replace_buttons(
        session,
        "3",
        [ButtonIn(label="Stop", custom_id="stop", callback_url="https://example.com/stop")],
    )

    assert await get_callback_url(session, "3", "go") is None
    assert await get_callback_url(session, "3", "stop") == "https://example.com/stop"


async def test_delete_message_data_removes_message_and_buttons(session):
    await save_message_and_buttons(
        session,
        "4",
        "100",
        [ButtonIn(label="Go", custom_id="go", callback_url="https://example.com/cb")],
    )

    await delete_message_data(session, "4")

    assert await get_channel_id(session, "4") is None
    assert await get_callback_url(session, "4", "go") is None
