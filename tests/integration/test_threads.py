AUTH_HEADERS = {"Authorization": "Bearer test-api-key"}


async def _create_message(client):
    response = await client.post(
        "/messages",
        json={"channel_id": "100", "content": "hello", "buttons": []},
        headers=AUTH_HEADERS,
    )
    return response.json()["message_id"]


async def test_create_thread_on_existing_message(client, fake_bot):
    message_id = await _create_message(client)

    response = await client.post(
        f"/messages/{message_id}/threads",
        json={"name": "logs de déploiement"},
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200
    thread_id = response.json()["thread_id"]
    assert thread_id
    create_call = fake_bot.calls[-1]
    assert create_call == ("create_thread", "100", message_id, "logs de déploiement", 1440)


async def test_create_thread_on_unknown_message_returns_404(client):
    response = await client.post(
        "/messages/does-not-exist/threads",
        json={"name": "logs"},
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 404


async def test_create_thread_requires_auth(client):
    response = await client.post(
        "/messages/123/threads",
        json={"name": "logs"},
    )

    assert response.status_code == 401


async def test_create_thread_rejects_invalid_auto_archive_duration(client, fake_bot):
    message_id = await _create_message(client)

    response = await client.post(
        f"/messages/{message_id}/threads",
        json={"name": "logs", "auto_archive_duration": 123},
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 422
