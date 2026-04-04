import pytest

from tests.conftest import make_token


@pytest.mark.asyncio
async def test_feed_detail_clap_and_track(client, db_session, seeded_data):
    user = seeded_data["user"]
    article = seeded_data["article"]
    token = make_token(user)

    feed_response = await client.get(f"/user/{user.id}/articles?sort=latest")
    assert feed_response.status_code == 200
    assert feed_response.json()["data"][0]["id"] == str(article.id)

    detail_response = await client.get(
        f"/articles/{article.id}?time_spent=6",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == article.title

    clap_response = await client.post(
        f"/articles/{article.id}/clap/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"userId": str(user.id), "count": 3},
    )
    assert clap_response.status_code == 200
    assert clap_response.json()["totalClaps"] == 5

    track_response = await client.post(
        f"/articles/{article.id}/track",
        headers={"Authorization": f"Bearer {token}"},
        json={"timeSpent": 9},
    )
    assert track_response.status_code == 200
    assert track_response.json()["tracked"] is True
