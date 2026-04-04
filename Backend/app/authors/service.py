import uuid

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.models import Article
from app.articles.schemas import ArticleListResponse
from app.articles.service import build_article_summaries
from app.auth.models import User
from app.authors.models import AuthorFollow
from app.authors.schemas import Author, AuthorListResponse, FollowStateResponse, FollowingItem, FollowingListResponse
from app.common.exceptions import bad_request, not_found
from app.common.pagination import PaginationMeta, paginate_scalars
from app.publications.models import Publication, PublicationFollow


async def _author_counts(db: AsyncSession, author_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict[str, int]]:
    counts = {
        author_id: {"followers": 0, "following": 0, "articles": 0}
        for author_id in author_ids
    }
    if not author_ids:
        return counts

    follower_rows = await db.execute(
        select(AuthorFollow.followed_id, func.count())
        .where(AuthorFollow.followed_id.in_(author_ids))
        .group_by(AuthorFollow.followed_id)
    )
    for author_id, count in follower_rows.all():
        counts[author_id]["followers"] = count

    following_rows = await db.execute(
        select(AuthorFollow.follower_id, func.count())
        .where(AuthorFollow.follower_id.in_(author_ids))
        .group_by(AuthorFollow.follower_id)
    )
    for author_id, count in following_rows.all():
        counts[author_id]["following"] = count

    article_rows = await db.execute(
        select(Article.author_id, func.count())
        .where(Article.author_id.in_(author_ids))
        .group_by(Article.author_id)
    )
    for author_id, count in article_rows.all():
        counts[author_id]["articles"] = count

    return counts


async def list_authors(
    db: AsyncSession,
    page: int,
    limit: int,
    current_user: User | None = None,
) -> AuthorListResponse:
    stmt = (
        select(User)
        .where(
            exists(
                select(1).where(Article.author_id == User.id)
            )
        )
        .order_by(User.name.asc())
    )
    if current_user is not None:
        stmt = stmt.where(User.id != current_user.id)

    users, pagination = await paginate_scalars(db, stmt, page, limit)
    counts = await _author_counts(db, [user.id for user in users])

    followed_author_ids: set[uuid.UUID] = set()
    if current_user is not None and users:
        followed_rows = await db.scalars(
            select(AuthorFollow.followed_id).where(
                AuthorFollow.follower_id == current_user.id,
                AuthorFollow.followed_id.in_([user.id for user in users]),
            )
        )
        followed_author_ids = set(followed_rows.all())

    data = [
        Author(
            id=user.id,
            name=user.name,
            avatar=user.avatar,
            bio=user.bio,
            followers=counts[user.id]["followers"],
            following=counts[user.id]["following"],
            articles=counts[user.id]["articles"],
            is_following=user.id in followed_author_ids,
        )
        for user in users
    ]
    return AuthorListResponse(data=data, pagination=pagination)


async def get_author(
    db: AsyncSession,
    author_id: uuid.UUID,
    current_user: User | None = None,
) -> Author:
    user = await db.get(User, author_id)
    if user is None:
        raise not_found("Author not found.")
    counts = await _author_counts(db, [author_id])
    author_counts = counts[author_id]

    is_following = False
    if current_user is not None:
        follow = await db.scalar(
            select(AuthorFollow).where(
                AuthorFollow.follower_id == current_user.id,
                AuthorFollow.followed_id == author_id,
            )
        )
        is_following = follow is not None

    return Author(
        id=user.id,
        name=user.name,
        avatar=user.avatar,
        bio=user.bio,
        followers=author_counts["followers"],
        following=author_counts["following"],
        articles=author_counts["articles"],
        is_following=is_following,
    )


async def list_author_articles(
    db: AsyncSession,
    author_id: uuid.UUID,
    page: int,
    limit: int,
) -> ArticleListResponse:
    user = await db.get(User, author_id)
    if user is None:
        raise not_found("Author not found.")
    articles, pagination = await paginate_scalars(
        db,
        select(Article).where(Article.author_id == author_id).order_by(Article.created_at.desc()),
        page,
        limit,
    )
    return ArticleListResponse(data=await build_article_summaries(db, articles), pagination=pagination)


async def list_following_entities(
    db: AsyncSession,
    user_id: uuid.UUID,
    follow_type: str | None,
    page: int,
    limit: int,
) -> FollowingListResponse:
    if await db.get(User, user_id) is None:
        raise not_found("User not found.")

    items: list[FollowingItem] = []
    if follow_type in (None, "author"):
        author_rows = await db.execute(
            select(User.name, User.avatar)
            .join(AuthorFollow, AuthorFollow.followed_id == User.id)
            .where(AuthorFollow.follower_id == user_id)
            .order_by(User.name.asc())
        )
        items.extend(
            FollowingItem(name=name, avatar=avatar, type="author")
            for name, avatar in author_rows.all()
        )

    if follow_type in (None, "publication"):
        publication_rows = await db.execute(
            select(Publication.name, Publication.avatar)
            .join(PublicationFollow, PublicationFollow.publication_id == Publication.id)
            .where(PublicationFollow.user_id == user_id)
            .order_by(Publication.name.asc())
        )
        items.extend(
            FollowingItem(name=name, avatar=avatar, type="publication")
            for name, avatar in publication_rows.all()
        )

    items.sort(key=lambda item: (item.type, item.name.lower()))
    total_items = len(items)
    start = (page - 1) * limit
    paged_items = items[start : start + limit]
    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total_items=total_items,
        total_pages=(total_items + limit - 1) // limit if total_items else 0,
    )
    return FollowingListResponse(data=paged_items, pagination=pagination)


async def follow_author(
    db: AsyncSession,
    author_id: uuid.UUID,
    user_id: uuid.UUID,
) -> FollowStateResponse:
    if author_id == user_id:
        raise bad_request("Users cannot follow themselves.")
    if await db.get(User, author_id) is None:
        raise not_found("Author not found.")
    if await db.get(User, user_id) is None:
        raise not_found("User not found.")

    follow = await db.scalar(
        select(AuthorFollow).where(
            AuthorFollow.follower_id == user_id,
            AuthorFollow.followed_id == author_id,
        )
    )
    if follow is None:
        db.add(AuthorFollow(follower_id=user_id, followed_id=author_id))
        await db.commit()

    follower_count = await db.scalar(
        select(func.count()).select_from(AuthorFollow).where(AuthorFollow.followed_id == author_id)
    )
    return FollowStateResponse(following=True, follower_count=follower_count or 0)


async def unfollow_author(
    db: AsyncSession,
    author_id: uuid.UUID,
    user_id: uuid.UUID,
) -> FollowStateResponse:
    follow = await db.scalar(
        select(AuthorFollow).where(
            AuthorFollow.follower_id == user_id,
            AuthorFollow.followed_id == author_id,
        )
    )
    if follow is not None:
        await db.delete(follow)
        await db.commit()
    follower_count = await db.scalar(
        select(func.count()).select_from(AuthorFollow).where(AuthorFollow.followed_id == author_id)
    )
    return FollowStateResponse(following=False, follower_count=follower_count or 0)
