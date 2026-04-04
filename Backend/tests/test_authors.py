import pytest

from tests.conftest import make_token


@pytest.mark.asyncio
async def test_authors_endpoint_only_lists_users_with_articles(client, seeded_data):
    user = seeded_data["user"]
    author = seeded_data["author"]
    token = make_token(user)

    response = await client.get(
        "/authors",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body["data"]] == [str(author.id)]
    assert body["data"][0]["articles"] == 1
