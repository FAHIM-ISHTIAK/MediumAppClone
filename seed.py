import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.articles.models import Article, ArticleTag, Clap, Tag
from app.articles.service import estimate_reading_time
from app.auth.models import User
from app.authors.models import AuthorFollow
from app.database import AsyncSessionFactory
from app.highlights.models import Highlight
from app.library.models import ReadingHistory, SavedArticle
from app.publications.models import Publication, PublicationFollow
from app.responses.models import InlineResponse, Response


USER_FIXTURES = [
    ("sarah.johnson@example.com", "Sarah Johnson"),
    ("omar.hassan@example.com", "Omar Hassan"),
    ("maya.chen@example.com", "Maya Chen"),
    ("liam.carter@example.com", "Liam Carter"),
    ("priya.nair@example.com", "Priya Nair"),
    ("noah.kim@example.com", "Noah Kim"),
    ("fatima.rahman@example.com", "Fatima Rahman"),
    ("daniel.morris@example.com", "Daniel Morris"),
    ("sofia.lee@example.com", "Sofia Lee"),
    ("ethan.ross@example.com", "Ethan Ross"),
]

PUBLICATION_FIXTURES = [
    ("Tech Insights", "tech-insights"),
    ("Data Science Collective", "data-science-collective"),
    ("Engineering Playbook", "engineering-playbook"),
    ("Design Forward", "design-forward"),
    ("Startup Notebook", "startup-notebook"),
]

TAG_NAMES = [
    "Web Development",
    "Machine Learning",
    "AI",
    "Python",
    "JavaScript",
    "Startups",
    "Data Science",
    "Cloud",
    "DevOps",
    "Productivity",
    "System Design",
    "React",
    "FastAPI",
    "Databases",
    "Design",
]

ARTICLE_TITLES = [
    "The Future of Web Development in 2026",
    "What AI Coding Assistants Change About Teamwork",
    "Why FastAPI Feels Right for Modern Backends",
    "How Small Teams Ship Bigger Products",
    "A Practical Guide to Postgres Indexing",
    "The Quiet Power of Great Documentation",
    "Making Search Feel Instant Without a Search Engine",
    "What Readers Actually Want From Product Blogs",
    "How We Reduced Backend Complexity by Half",
    "Building Better Reading Analytics",
    "The Design Habits of Strong Engineering Teams",
    "Scaling APIs Without Losing Developer Joy",
    "How to Think About Follow Systems",
    "Lessons From Building a Personal Library Feature",
    "Why Recommendations Should Still Feel Human",
    "Finding the Right Shape for Inline Discussions",
    "Choosing Simplicity Over Cleverness in SQL",
    "What Makes a Publication Feel Trustworthy",
    "The Anatomy of a Great Home Feed",
    "Working With Rich Text Without Regret",
    "How Async Python Improves Developer Experience",
    "Why Bookmarking Is More Important Than It Looks",
    "Designing APIs That Age Well",
    "A Better Way to Structure Service Layers",
    "What Good Seed Data Looks Like",
    "How to Measure Reading Time Honestly",
    "Creating Author Profiles Readers Care About",
    "The Hidden Cost of Poor Search Ranking",
    "Building Comment Systems With Fewer Surprises",
    "From Prototype to Production Without Panic",
]

COMMENT_SNIPPETS = [
    "Really insightful breakdown. The examples made the tradeoffs much clearer.",
    "This matches our experience almost exactly, especially around keeping the API small.",
    "I appreciate how practical this feels. It is rare to see the edge cases covered this well.",
    "The section on implementation details was especially helpful.",
    "I would love a follow-up on how this works at larger scale.",
]

INLINE_NOTES = [
    "Great framing for the rest of the article.",
    "This paragraph captures the problem perfectly.",
    "Strong point. This is where the design really clicks.",
    "Worth expanding into its own article.",
]

HIGHLIGHT_COLORS = ["yellow", "green", "blue", "pink", "purple"]


def build_paragraphs(title: str) -> list[str]:
    return [
        f"{title} starts with a simple observation: the best product experiences feel calm, even when the implementation behind them is not.",
        "Teams make better decisions when they keep the reader's journey visible from the first database table to the final interface.",
        "In practice that means favoring clear data shapes, predictable APIs, and feedback loops that are easy to reason about.",
        "The technical details matter, but they matter most when they preserve momentum for both the product team and the user.",
        "A strong backend should make the frontend simpler, not force it to negotiate every edge case on its own.",
        "That is why thoughtful schemas, small services, and reliable analytics are worth the upfront effort.",
    ]


async def main() -> None:
    random.seed(42)
    async with AsyncSessionFactory() as session:
        existing_users = await session.scalar(select(User.id).limit(1))
        if existing_users is not None:
            print("Seed skipped: database already contains users.")
            return

        now = datetime.now(timezone.utc)

        users: list[User] = []
        for index, (email, name) in enumerate(USER_FIXTURES, start=1):
            users.append(
                User(
                    id=uuid.uuid5(uuid.NAMESPACE_DNS, email),
                    email=email,
                    name=name,
                    avatar=f"https://images.unsplash.com/photo-{1510000000000 + index}?w=150&h=150&fit=crop",
                    bio=f"{name} writes about software, product thinking, and building internet tools people enjoy using.",
                )
            )
        session.add_all(users)

        publications: list[Publication] = []
        for index, (name, slug) in enumerate(PUBLICATION_FIXTURES, start=1):
            publications.append(
                Publication(
                    id=uuid.uuid5(uuid.NAMESPACE_DNS, slug),
                    name=name,
                    slug=slug,
                    description=f"{name} publishes practical essays on modern software, product, and internet culture.",
                    avatar=f"https://images.unsplash.com/photo-{1520000000000 + index}?w=150&h=150&fit=crop",
                )
            )
        session.add_all(publications)

        tags = [Tag(id=uuid.uuid5(uuid.NAMESPACE_DNS, name), name=name) for name in TAG_NAMES]
        session.add_all(tags)
        
        await session.flush()

        articles: list[Article] = []
        for index, title in enumerate(ARTICLE_TITLES):
            subtitle = f"A practical look at {title.lower()} for teams building modern reading experiences."
            content = build_paragraphs(title)
            article = Article(
                id=uuid.uuid4(),
                title=title,
                subtitle=subtitle,
                author_id=random.choice(users).id,
                publication_id=random.choice(publications).id if index % 4 != 0 else None,
                content=content,
                cover_image=f"https://images.unsplash.com/photo-{1530000000000 + index}?w=800&h=400&fit=crop",
                reading_time=estimate_reading_time(content),
                created_at=now - timedelta(days=index * 2),
                updated_at=now - timedelta(days=index * 2),
            )
            articles.append(article)
        session.add_all(articles)
        await session.flush()

        article_tags: list[ArticleTag] = []
        for article in articles:
            for tag in random.sample(tags, random.randint(2, 4)):
                article_tags.append(ArticleTag(article_id=article.id, tag_id=tag.id))
        session.add_all(article_tags)

        clap_pairs = random.sample(
            [(user.id, article.id) for user in users for article in articles],
            k=100,
        )
        claps: list[Clap] = []
        for user_id, article_id in clap_pairs:
            count = random.randint(1, 50)
            article = next(item for item in articles if item.id == article_id)
            article.clap_count += count
            claps.append(Clap(article_id=article_id, user_id=user_id, count=count))
        session.add_all(claps)

        responses: list[Response] = []
        for index in range(40):
            article = random.choice(articles)
            response = Response(
                id=uuid.uuid4(),
                article_id=article.id,
                user_id=random.choice(users).id,
                text=random.choice(COMMENT_SNIPPETS),
                likes=random.randint(0, 30),
                created_at=now - timedelta(days=random.randint(0, 60)),
                updated_at=now - timedelta(days=random.randint(0, 60)),
            )
            article.response_count += 1
            responses.append(response)
        session.add_all(responses)

        inline_responses: list[InlineResponse] = []
        for _ in range(20):
            article = random.choice(articles)
            paragraph_index = random.randint(0, len(article.content) - 1)
            inline_responses.append(
                InlineResponse(
                    id=uuid.uuid4(),
                    article_id=article.id,
                    user_id=random.choice(users).id,
                    selected_text=article.content[paragraph_index][:90],
                    paragraph_index=paragraph_index,
                    text=random.choice(INLINE_NOTES),
                    likes=random.randint(0, 10),
                    created_at=now - timedelta(days=random.randint(0, 60)),
                    updated_at=now - timedelta(days=random.randint(0, 60)),
                )
            )
        session.add_all(inline_responses)

        highlights: list[Highlight] = []
        for _ in range(30):
            article = random.choice(articles)
            paragraph_index = random.randint(0, len(article.content) - 1)
            highlights.append(
                Highlight(
                    id=uuid.uuid4(),
                    article_id=article.id,
                    user_id=random.choice(users).id,
                    text=article.content[paragraph_index][:100],
                    color=random.choice(HIGHLIGHT_COLORS),
                    paragraph_index=paragraph_index,
                    created_at=now - timedelta(days=random.randint(0, 45)),
                )
            )
        session.add_all(highlights)

        author_follow_pairs = set()
        while len(author_follow_pairs) < 25:
            follower = random.choice(users).id
            followed = random.choice(users).id
            if follower != followed:
                author_follow_pairs.add((follower, followed))
        session.add_all(
            [
                AuthorFollow(follower_id=follower_id, followed_id=followed_id)
                for follower_id, followed_id in author_follow_pairs
            ]
        )

        publication_follow_pairs = random.sample(
            [(user.id, publication.id) for user in users for publication in publications],
            k=20,
        )
        session.add_all(
            [
                PublicationFollow(user_id=user_id, publication_id=publication_id)
                for user_id, publication_id in publication_follow_pairs
            ]
        )

        history_entries: list[ReadingHistory] = []
        for _ in range(60):
            article = random.choice(articles)
            read_at = now - timedelta(days=random.randint(0, 90), minutes=random.randint(0, 1440))
            history_entries.append(
                ReadingHistory(
                    id=uuid.uuid4(),
                    user_id=random.choice(users).id,
                    article_id=article.id,
                    time_spent=random.randint(2, 18),
                    read_at=read_at,
                )
            )
        session.add_all(history_entries)

        saved_pairs = random.sample(
            [(user.id, article.id) for user in users for article in articles],
            k=15,
        )
        session.add_all(
            [
                SavedArticle(user_id=user_id, article_id=article_id)
                for user_id, article_id in saved_pairs
            ]
        )

        await session.commit()
        print("Seed complete: 10 users, 5 publications, 15 tags, 30 articles, and related activity created.")


if __name__ == "__main__":
    asyncio.run(main())
