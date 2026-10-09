async def test_healthz_returns_ok_without_auth(client):
    response = await client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
