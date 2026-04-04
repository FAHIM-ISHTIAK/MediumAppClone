from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url


SUPABASE_TRANSACTION_POOLER_PORT = 6543
SUPABASE_SESSION_POOLER_PORT = 5432


def _parse_database_url(raw_url: str) -> URL | None:
    try:
        return make_url(raw_url)
    except Exception:
        return None


def _is_supabase_pooler_url(raw_url: str) -> bool:
    parsed = _parse_database_url(raw_url)
    return bool(parsed and parsed.host and parsed.host.endswith("pooler.supabase.com"))


def _is_supabase_transaction_pooler_url(raw_url: str) -> bool:
    parsed = _parse_database_url(raw_url)
    return bool(
        parsed
        and parsed.host
        and parsed.host.endswith("pooler.supabase.com")
        and parsed.port == SUPABASE_TRANSACTION_POOLER_PORT
    )


def _swap_database_port(raw_url: str, port: int) -> str:
    parsed = _parse_database_url(raw_url)
    if parsed is None:
        return raw_url
    return parsed.set(port=port).render_as_string(hide_password=False)


def _set_database_query_params(raw_url: str, params: dict[str, str]) -> str:
    parsed = _parse_database_url(raw_url)
    if parsed is None:
        return raw_url
    return parsed.update_query_dict(params).render_as_string(hide_password=False)


class Settings(BaseSettings):
    app_name: str = "Medium Clone API"
    api_prefix: str = ""
    debug: str | bool = False
    database_url: str = Field(
        default="sqlite+aiosqlite:///./medium_clone.db",
        alias="DATABASE_URL",
    )
    supabase_jwt_secret: str = Field(default="dev-secret", alias="SUPABASE_JWT_SECRET")
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")
    database_direct_url: str | None = Field(default=None, alias="DATABASE_DIRECT_URL")
    database_connection_mode: Literal["auto", "direct", "session", "transaction"] = Field(
        default="auto",
        alias="DATABASE_CONNECTION_MODE",
    )
    db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=10, alias="DB_POOL_TIMEOUT")
    db_pool_recycle: int = Field(default=300, alias="DB_POOL_RECYCLE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def frontend_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_url.split(",") if origin.strip()]

    @property
    def effective_database_url(self) -> str:
        if self.database_connection_mode == "direct" and self.database_direct_url:
            return self.database_direct_url

        if self.database_connection_mode == "session" and _is_supabase_pooler_url(self.database_url):
            return _swap_database_port(self.database_url, SUPABASE_SESSION_POOLER_PORT)

        if self.database_connection_mode == "transaction":
            return self.database_url

        if self.database_direct_url:
            return self.database_direct_url

        if _is_supabase_transaction_pooler_url(self.database_url):
            return _swap_database_port(self.database_url, SUPABASE_SESSION_POOLER_PORT)

        return self.database_url

    @property
    def uses_transaction_pooler(self) -> bool:
        return _is_supabase_transaction_pooler_url(self.effective_database_url)

    @property
    def uses_supabase_pooler(self) -> bool:
        return _is_supabase_pooler_url(self.effective_database_url)

    @property
    def uses_postgres(self) -> bool:
        return self.effective_database_url.startswith(("postgresql://", "postgres://"))

    @property
    def should_use_app_pool(self) -> bool:
        return self.uses_postgres and not self.uses_transaction_pooler

    @property
    def async_database_url(self) -> str:
        url = self.effective_database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)

        if self.uses_transaction_pooler:
            url = _set_database_query_params(url, {"prepared_statement_cache_size": "0"})

        return url

    @property
    def async_engine_kwargs(self) -> dict:
        import uuid

        kwargs: dict = {}
        if self.async_database_url.startswith("postgresql+asyncpg://") and self.uses_supabase_pooler:
            kwargs["connect_args"] = {
                "statement_cache_size": 0,
                "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
            }
        return kwargs

    @property
    def debug_enabled(self) -> bool:
        if isinstance(self.debug, bool):
            return self.debug
        return self.debug.strip().lower() in {"1", "true", "yes", "on", "debug"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
