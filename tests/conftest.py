import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone

from jose import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.articles.models import Article, ArticleTag, Tag
from app.articles.service import estimate_reading_time
from app.auth.models import User
from app.config import settings
from app.database import Base
from app.dependencies import get_db
from app.main import app
from app.publications.models import Publication


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def seeded_data(db_session: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        email="reader@example.com",
        name="Reader One",
        avatar="https://example.com/reader.png",
        bio="Enjoys reading product and engineering essays.",
    )
    author = User(
        id=uuid.uuid4(),
        email="author@example.com",
        name="Author Two",
        avatar="https://example.com/author.png",
        bio="Writes about backend systems.",
    )
    publication = Publication(
        id=uuid.uuid4(),
        name="Tech Insights",
        slug="tech-insights",
        description="Thoughtful essays about software systems.",
        avatar="https://example.com/publication.png",
    )
    tag_fastapi = Tag(id=uuid.uuid4(), name="FastAPI")
    tag_python = Tag(id=uuid.uuid4(), name="Python")
    content = [
        "FastAPI lets teams move quickly without giving up API clarity.",
        "When paired with good schema design, it stays maintainable.",
        "That combination matters in content products where the API surface grows fast.",
    ]
    article = Article(
        id=uuid.uuid4(),
        title="FastAPI for Reader Products",
        subtitle="How small backend choices shape the reading experience",
        author_id=author.id,
        publication_id=publication.id,
        content=content,
        cover_image="https://example.com/article.png",
        reading_time=estimate_reading_time(content),
        clap_count=2,
        response_count=0,
        created_at=datetime.now(timezone.utc) - timedelta(days=1),
        updated_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add_all([user, author, publication, tag_fastapi, tag_python, article])
    db_session.add_all(
        [
            ArticleTag(article_id=article.id, tag_id=tag_fastapi.id),
            ArticleTag(article_id=article.id, tag_id=tag_python.id),
        ]
    )
    await db_session.commit()
    return {
        "user": user,
        "author": author,
        "publication": publication,
        "article": article,
        "tags": [tag_fastapi, tag_python],
    }


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client
    app.dependency_overrides.clear()


def make_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "aud": "authenticated",
        "exp": now + timedelta(hours=1),
        "user_metadata": {
            "full_name": user.name,
            "avatar_url": user.avatar,
        },
    }
    return jwt.encode(payload, settings.supabase_jwt_secret, algorithm="HS256")
