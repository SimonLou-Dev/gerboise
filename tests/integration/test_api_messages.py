from gerboise.buttons_service import get_channel_id

AUTH_HEADERS = {"Authorization": "Bearer test-api-key"}


async def _create_message(client, buttons=None):
    response = await client.post(
        "/messages",
        json={
            "channel_id": "100",
            "content": "hello",
            "buttons": buttons or [],
        },
        headers=AUTH_HEADERS,
    )
    return response


async def test_post_message_requires_auth(client):
    response = await client.post(
        "/messages", json={"channel_id": "100", "content": "hello", "buttons": []}
    )

    assert response.status_code == 401


async def test_post_message_creates_message_and_registers_buttons(client, fake_bot, session):
    response = await _create_message(
        client,
        buttons=[{"label": "Go", "custom_id": "go", "callback_url": "https://example.com/cb"}],
    )

    assert response.status_code == 200
    message_id = response.json()["message_id"]
    post_call = fake_bot.calls[0]
    assert post_call[0] == "post"
    assert post_call[1] == "100"
    assert post_call[2] == "hello"
    assert post_call[3][0].custom_id == "go"
    assert await get_channel_id(session, message_id) == "100"


async def test_patch_message_content_only_leaves_buttons_untouched(client, fake_bot):
    created = await _create_message(
        client,
        buttons=[{"label": "Go", "custom_id": "go", "callback_url": "https://example.com/cb"}],
    )
    message_id = created.json()["message_id"]

    response = await client.patch(
        f"/messages/{message_id}", json={"content": "updated"}, headers=AUTH_HEADERS
    )

    assert response.status_code == 200
    edit_call = fake_bot.calls[-1]
    assert edit_call == ("edit", "100", message_id, "updated", None)


async def test_patch_message_replaces_buttons(client, fake_bot):
    created = await _create_message(
        client,
        buttons=[{"label": "Go", "custom_id": "go", "callback_url": "https://example.com/cb"}],
    )
    message_id = created.json()["message_id"]

    response = await client.patch(
        f"/messages/{message_id}",
        json={
            "buttons": [
                {"label": "Stop", "custom_id": "stop", "callback_url": "https://example.com/stop"}
            ]
        },
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200
    edit_call = fake_bot.calls[-1]
    assert edit_call[0] == "edit"
    new_buttons = edit_call[4]
    assert new_buttons[0].custom_id == "stop"


async def test_patch_unknown_message_returns_404(client):
    response = await client.patch(
        "/messages/does-not-exist", json={"content": "x"}, headers=AUTH_HEADERS
    )

    assert response.status_code == 404


async def test_delete_message_is_idempotent(client, fake_bot, session):
    created = await _create_message(client)
    message_id = created.json()["message_id"]

    first_delete = await client.delete(f"/messages/{message_id}", headers=AUTH_HEADERS)
    assert first_delete.status_code == 200
    assert fake_bot.calls[-1] == ("delete", "100", message_id)
    assert await get_channel_id(session, message_id) is None

    second_delete = await client.delete(f"/messages/{message_id}", headers=AUTH_HEADERS)
    assert second_delete.status_code == 200
    # message already gone from our DB: bot.delete_message is not called a second time
    assert fake_bot.calls[-1] == ("delete", "100", message_id)
