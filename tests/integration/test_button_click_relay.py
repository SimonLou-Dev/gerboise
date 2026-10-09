import httpx
import respx
from discord import InteractionType

from gerboise.buttons_service import save_message_and_buttons
from gerboise.discord_bot import GerboiseBot
from gerboise.schemas import ButtonIn


class FakeResponse:
    def __init__(self) -> None:
        self.deferred = False

    async def defer(self) -> None:
        self.deferred = True


class FakeMessage:
    def __init__(self, message_id: int) -> None:
        self.id = message_id


class FakeUser:
    def __init__(self, user_id: int, name: str) -> None:
        self.id = user_id
        self.name = name


class FakeInteraction:
    def __init__(self, message_id: int, custom_id: str, user_id: int, username: str) -> None:
        self.type = InteractionType.component
        self.message = FakeMessage(message_id)
        self.data = {"custom_id": custom_id}
        self.user = FakeUser(user_id, username)
        self.response = FakeResponse()


@respx.mock
async def test_button_click_relays_to_callback_url(session_factory, session):
    await save_message_and_buttons(
        session,
        "42",
        "100",
        [ButtonIn(label="Go", custom_id="go", callback_url="https://example.com/cb")],
    )

    route = respx.post("https://example.com/cb").mock(return_value=httpx.Response(200))

    bot = GerboiseBot(session_factory=session_factory)
    interaction = FakeInteraction(message_id=42, custom_id="go", user_id=7, username="simon")

    await bot.on_interaction(interaction)

    assert interaction.response.deferred is True
    assert route.called
    sent_body = route.calls.last.request.content
    assert b'"message_id":"42"' in sent_body
    assert b'"custom_id":"go"' in sent_body


@respx.mock
async def test_button_click_without_known_callback_is_ignored(session_factory, session):
    route = respx.post("https://example.com/cb").mock(return_value=httpx.Response(200))

    bot = GerboiseBot(session_factory=session_factory)
    interaction = FakeInteraction(message_id=999, custom_id="unknown", user_id=7, username="simon")

    await bot.on_interaction(interaction)

    assert interaction.response.deferred is True
    assert not route.called
