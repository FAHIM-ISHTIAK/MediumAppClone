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

    story_search_response = await client.get("/search?q=api&type=stories")
    assert story_search_response.status_code == 200
    assert story_search_response.json()["stories"]["total"] >= 1

    # Story search should only match article titles.
    subtitle_only_search_response = await client.get("/search?q=backend&type=stories")
    assert subtitle_only_search_response.status_code == 200
    assert subtitle_only_search_response.json()["stories"]["total"] == 0

    author_name_story_search_response = await client.get("/search?q=author&type=stories")
    assert author_name_story_search_response.status_code == 200
    assert author_name_story_search_response.json()["stories"]["total"] == 0

    author_search_response = await client.get("/search?q=thor&type=people")
    assert author_search_response.status_code == 200
    assert author_search_response.json()["people"]["total"] >= 1

    publication_search_response = await client.get("/search?q=ech&type=publications")
    assert publication_search_response.status_code == 200
    assert publication_search_response.json()["publications"]["total"] >= 1

    combined_search_response = await client.get("/search?q=t")
    assert combined_search_response.status_code == 200
    combined_search_body = combined_search_response.json()
    assert combined_search_body["stories"]["total"] >= 1
    assert combined_search_body["people"]["total"] >= 1
    assert combined_search_body["publications"]["total"] >= 1

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
