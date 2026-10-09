import httpx
import respx

from gerboise.callback import relay_click
from gerboise.schemas import ClickPayload, ClickUser


def _payload() -> ClickPayload:
    return ClickPayload(
        message_id="1",
        custom_id="go",
        user=ClickUser(id="42", username="simon"),
        clicked_at="2024-01-01T00:00:00Z",
    )


@respx.mock
async def test_relay_click_posts_payload():
    route = respx.post("https://example.com/cb").mock(return_value=httpx.Response(200))

    await relay_click("https://example.com/cb", _payload())

    assert route.called
    sent_body = route.calls.last.request.content
    assert b'"custom_id":"go"' in sent_body


@respx.mock
async def test_relay_click_swallows_http_errors():
    respx.post("https://example.com/cb").mock(return_value=httpx.Response(500))

    await relay_click("https://example.com/cb", _payload())
