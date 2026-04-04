import uuid

import pytest

from app.auth.models import User
from tests.conftest import make_token


@pytest.mark.asyncio
async def test_auth_sync_and_me(client, db_session):
    user = User(
        id=uuid.uuid4(),
        email="sync@example.com",
        name="Sync Placeholder",
        avatar="https://example.com/sync.png",
        bio=None,
    )
    token = make_token(user)

    response = await client.post("/auth/sync", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "sync@example.com"
    assert body["name"] == "Sync Placeholder"

    me_response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["id"] == str(user.id)
