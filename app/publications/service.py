import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.models import Article
from app.articles.schemas import ArticleListResponse
from app.articles.service import build_article_summaries
from app.common.exceptions import not_found
from app.common.pagination import paginate_scalars
from app.publications.models import Publication, PublicationFollow
from app.publications.schemas import FollowPublicationResponse, Publication as PublicationSchema
from app.publications.schemas import PublicationListResponse


async def _publication_counts(
    db: AsyncSession,
    publication_ids: list[uuid.UUID],
) -> dict[uuid.UUID, dict[str, int]]:
    counts = {publication_id: {"followers": 0, "articles_count": 0} for publication_id in publication_ids}
    if not publication_ids:
        return counts

    follower_rows = await db.execute(
        select(PublicationFollow.publication_id, func.count())
        .where(PublicationFollow.publication_id.in_(publication_ids))
        .group_by(PublicationFollow.publication_id)
    )
    for publication_id, count in follower_rows.all():
        counts[publication_id]["followers"] = count

    article_rows = await db.execute(
        select(Article.publication_id, func.count())
        .where(Article.publication_id.in_(publication_ids))
        .group_by(Article.publication_id)
    )
    for publication_id, count in article_rows.all():
        counts[publication_id]["articles_count"] = count
    return counts


async def list_publications(db: AsyncSession, page: int, limit: int) -> PublicationListResponse:
    publications, pagination = await paginate_scalars(
        db,
        select(Publication).order_by(Publication.name.asc()),
        page,
        limit,
    )
    counts = await _publication_counts(db, [publication.id for publication in publications])
    data = [
        PublicationSchema(
            id=publication.id,
            name=publication.name,
            description=publication.description,
            avatar=publication.avatar,
            followers=counts[publication.id]["followers"],
            articles_count=counts[publication.id]["articles_count"],
        )
        for publication in publications
    ]
    return PublicationListResponse(data=data, pagination=pagination)


async def get_publication(db: AsyncSession, publication_id: uuid.UUID) -> PublicationSchema:
    publication = await db.get(Publication, publication_id)
    if publication is None:
        raise not_found("Publication not found.")
    counts = await _publication_counts(db, [publication_id])
    publication_counts = counts[publication_id]
    return PublicationSchema(
        id=publication.id,
        name=publication.name,
        description=publication.description,
        avatar=publication.avatar,
        followers=publication_counts["followers"],
        articles_count=publication_counts["articles_count"],
    )


async def list_publication_articles(
    db: AsyncSession,
    publication_id: uuid.UUID,
    page: int,
    limit: int,
) -> ArticleListResponse:
    if await db.get(Publication, publication_id) is None:
        raise not_found("Publication not found.")
    articles, pagination = await paginate_scalars(
        db,
        select(Article)
        .where(Article.publication_id == publication_id)
        .order_by(Article.created_at.desc()),
        page,
        limit,
    )
    return ArticleListResponse(data=await build_article_summaries(db, articles), pagination=pagination)


async def follow_publication(
    db: AsyncSession,
    publication_id: uuid.UUID,
    user_id: uuid.UUID,
) -> FollowPublicationResponse:
    if await db.get(Publication, publication_id) is None:
        raise not_found("Publication not found.")
    follow = await db.scalar(
        select(PublicationFollow).where(
            PublicationFollow.user_id == user_id,
            PublicationFollow.publication_id == publication_id,
        )
    )
    if follow is None:
        db.add(PublicationFollow(user_id=user_id, publication_id=publication_id))
        await db.commit()
    follower_count = await db.scalar(
        select(func.count())
        .select_from(PublicationFollow)
        .where(PublicationFollow.publication_id == publication_id)
    )
    return FollowPublicationResponse(following=True, follower_count=follower_count or 0)


async def unfollow_publication(
    db: AsyncSession,
    publication_id: uuid.UUID,
    user_id: uuid.UUID,
) -> FollowPublicationResponse:
    follow = await db.scalar(
        select(PublicationFollow).where(
            PublicationFollow.user_id == user_id,
            PublicationFollow.publication_id == publication_id,
        )
    )
    if follow is not None:
        await db.delete(follow)
        await db.commit()
    follower_count = await db.scalar(
        select(func.count())
        .select_from(PublicationFollow)
        .where(PublicationFollow.publication_id == publication_id)
    )
    return FollowPublicationResponse(following=False, follower_count=follower_count or 0)
