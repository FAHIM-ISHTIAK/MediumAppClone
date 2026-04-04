from app.config import Settings


SUPABASE_TRANSACTION_URL = (
    "postgresql://postgres.demo-ref:secret@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
)
SUPABASE_DIRECT_URL = "postgresql://postgres:secret@db.demo-ref.supabase.co:5432/postgres"


def test_auto_mode_promotes_transaction_pooler_to_session_mode():
    settings = Settings(_env_file=None, DATABASE_URL=SUPABASE_TRANSACTION_URL)

    assert settings.effective_database_url.endswith(":5432/postgres")
    assert settings.uses_supabase_pooler is True
    assert settings.uses_transaction_pooler is False
    assert settings.should_use_app_pool is True
    assert "prepared_statement_cache_size=0" not in settings.async_database_url


def test_transaction_mode_preserves_transaction_pooler_safeguards():
    settings = Settings(
        _env_file=None,
        DATABASE_URL=SUPABASE_TRANSACTION_URL,
        DATABASE_CONNECTION_MODE="transaction",
    )

    assert settings.effective_database_url.endswith(":6543/postgres")
    assert settings.uses_transaction_pooler is True
    assert settings.should_use_app_pool is False
    assert "prepared_statement_cache_size=0" in settings.async_database_url
    assert settings.async_engine_kwargs["connect_args"]["statement_cache_size"] == 0


def test_auto_mode_prefers_direct_url_when_available():
    settings = Settings(
        _env_file=None,
        DATABASE_URL=SUPABASE_TRANSACTION_URL,
        DATABASE_DIRECT_URL=SUPABASE_DIRECT_URL,
    )

    assert settings.effective_database_url == SUPABASE_DIRECT_URL
    assert settings.uses_supabase_pooler is False
    assert settings.uses_transaction_pooler is False
    assert settings.should_use_app_pool is True
