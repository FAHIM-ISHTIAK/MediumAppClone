import pytest

from app.library.models import SavedArticle
from tests.conftest import make_token


@pytest.mark.asyncio
async def test_search_and_analytics(client, seeded_data):
    user = seeded_data["user"]
    article = seeded_data["article"]
    token = make_token(user)

    await client.get(
        f"/articles/{article.id}?time_spent=4",
        headers={"Authorization": f"Bearer {token}"},
    )

    search_response = await client.get("/search?q=FastAPI&type=stories")
    assert search_response.status_code == 200
    assert search_response.json()["stories"]["total"] >= 1

    analytics_response = await client.get(
        f"/users/{user.id}/library/history/analytics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert analytics_response.status_code == 200
    body = analytics_response.json()
    assert body["totalArticlesRead"] >= 1
    assert body["totalTimeSpentMinutes"] >= 0

    history_response = await client.get(
        f"/users/{user.id}/library/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert history_response.status_code == 200
    assert history_response.json()["data"][0]["articleId"] == str(article.id)


@pytest.mark.asyncio
async def test_saved_article_state_endpoint(client, db_session, seeded_data):
    user = seeded_data["user"]
    article = seeded_data["article"]
    token = make_token(user)

    db_session.add(SavedArticle(user_id=user.id, article_id=article.id))
    await db_session.commit()

    response = await client.get(
        f"/users/{user.id}/library/saved/{article.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "saved": True,
        "articleId": str(article.id),
    }
