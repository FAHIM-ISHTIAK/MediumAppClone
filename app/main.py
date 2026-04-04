from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401
from app.articles.router import router as articles_router
from app.auth.router import router as auth_router
from app.authors.router import router as authors_router
from app.config import settings
from app.highlights.router import router as highlights_router
from app.library.router import router as library_router
from app.publications.router import router as publications_router
from app.responses.router import router as responses_router
from app.search.router import router as search_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.frontend_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(articles_router, prefix=settings.api_prefix)
    app.include_router(responses_router, prefix=settings.api_prefix)
    app.include_router(highlights_router, prefix=settings.api_prefix)
    app.include_router(authors_router, prefix=settings.api_prefix)
    app.include_router(publications_router, prefix=settings.api_prefix)
    app.include_router(search_router, prefix=settings.api_prefix)
    app.include_router(library_router, prefix=settings.api_prefix)

    return app


app = create_app()
