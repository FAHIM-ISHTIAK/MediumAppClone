from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.models import Article
from app.articles.service import build_article_summaries
from app.auth.models import User
from app.authors.schemas import Author
from app.authors.service import _author_counts
from app.common.pagination import PaginationMeta
from app.publications.models import Publication
from app.publications.schemas import Publication as PublicationSchema
from app.publications.service import _publication_counts
from app.search.schemas import SearchResponse, SearchSection


async def search(db: AsyncSession, q: str, type_: str | None, page: int, limit: int) -> SearchResponse:
    pattern = f"%{q.strip()}%"
    pagination = PaginationMeta(page=page, limit=limit, total_items=0, total_pages=0)
    response = SearchResponse(pagination=pagination)

    if type_ in (None, "stories"):
        article_stmt = (
            select(Article)
            .where(or_(Article.title.ilike(pattern), Article.subtitle.ilike(pattern)))
            .order_by(Article.created_at.desc())
        )
        article_total = await db.scalar(select(func.count()).select_from(article_stmt.subquery())) or 0
        articles = (
            await db.scalars(article_stmt.offset((page - 1) * limit).limit(limit))
        ).all()
        response.stories = SearchSection(data=await build_article_summaries(db, articles), total=article_total)
        response.pagination.total_items = max(response.pagination.total_items, article_total)

    if type_ in (None, "people"):
        people_stmt = select(User).where(User.name.ilike(pattern)).order_by(User.name.asc())
        people_total = await db.scalar(select(func.count()).select_from(people_stmt.subquery())) or 0
        people = (await db.scalars(people_stmt.offset((page - 1) * limit).limit(limit))).all()
        counts = await _author_counts(db, [person.id for person in people])
        response.people = SearchSection(
            data=[
                Author(
                    id=person.id,
                    name=person.name,
                    avatar=person.avatar,
                    bio=person.bio,
                    followers=counts[person.id]["followers"],
                    following=counts[person.id]["following"],
                    articles=counts[person.id]["articles"],
                )
                for person in people
            ],
            total=people_total,
        )
        response.pagination.total_items = max(response.pagination.total_items, people_total)

    if type_ in (None, "publications"):
        publication_stmt = select(Publication).where(Publication.name.ilike(pattern)).order_by(Publication.name.asc())
        publication_total = await db.scalar(select(func.count()).select_from(publication_stmt.subquery())) or 0
        publications = (
            await db.scalars(publication_stmt.offset((page - 1) * limit).limit(limit))
        ).all()
        counts = await _publication_counts(db, [publication.id for publication in publications])
        response.publications = SearchSection(
            data=[
                PublicationSchema(
                    id=publication.id,
                    name=publication.name,
                    description=publication.description,
                    avatar=publication.avatar,
                    followers=counts[publication.id]["followers"],
                    articles_count=counts[publication.id]["articles_count"],
                )
                for publication in publications
            ],
            total=publication_total,
        )
        response.pagination.total_items = max(response.pagination.total_items, publication_total)

    response.pagination.total_pages = (
        (response.pagination.total_items + limit - 1) // limit if response.pagination.total_items else 0
    )
    return response
