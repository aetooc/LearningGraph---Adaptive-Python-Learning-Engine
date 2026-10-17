import pytest
from sqlalchemy.engine import make_url

pytest.importorskip("pydantic_settings")

from pydantic import ValidationError

from app.config import Settings


@pytest.mark.parametrize("scheme", ["postgres", "postgresql"])
def test_cloud_database_urls_use_installed_driver_and_preserve_connection_options(scheme):
    settings = Settings(database_url=(
        f"{scheme}://demo:encoded%40password@db.example.com:5432/learning"
        "?sslmode=require&channel_binding=require"
    ))
    url = make_url(settings.database_url)
    assert url.drivername == "postgresql+psycopg"
    assert url.username == "demo"
    assert url.password == "encoded@password"
    assert url.host == "db.example.com"
    assert url.database == "learning"
    assert url.query == {"sslmode": "require", "channel_binding": "require"}


@pytest.mark.parametrize("url", [
    "sqlite:///:memory:",
    "postgresql+psycopg://demo:password@localhost:5433/learning",
])
def test_explicit_driver_and_test_database_urls_are_preserved(url):
    assert Settings(database_url=url).database_url == url


def test_public_frontend_origins_are_read_as_json_from_environment(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["https://learninggraph.vercel.app"]')
    assert Settings().cors_origins == ["https://learninggraph.vercel.app"]


@pytest.fixture
def isolated_llm_environment(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    for prefix in ("OPENAI", "GROQ"):
        for suffix in ("API_KEY", "MODEL", "BASE_URL"):
            monkeypatch.delenv(f"{prefix}_{suffix}", raising=False)


def test_llm_defaults_to_openai_without_requiring_credentials(isolated_llm_environment):
    settings = Settings()

    assert settings.llm_provider == "openai"
    assert settings.llm.name == "OpenAI"
    assert settings.llm.api_key is None
    assert settings.llm.model is None
    assert settings.llm.base_url == "https://api.openai.com/v1"
    assert settings.groq_base_url == "https://api.groq.com/openai/v1"


@pytest.mark.parametrize("provider,name,base_url", [
    ("openai", "OpenAI", "https://api.openai.com/v1"),
    ("groq", "Groq", "https://api.groq.com/openai/v1"),
])
def test_environment_selects_provider_credentials_and_default_endpoint(
    isolated_llm_environment, monkeypatch, provider, name, base_url,
):
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setenv("OPENAI_MODEL", "openai-test-model")
    monkeypatch.setenv("GROQ_API_KEY", "groq-test-key")
    monkeypatch.setenv("GROQ_MODEL", "groq-test-model")

    llm = Settings().llm

    assert llm.name == name
    assert llm.api_key.get_secret_value() == f"{provider}-test-key"
    assert llm.model == f"{provider}-test-model"
    assert llm.base_url == base_url
    assert llm.api_key_setting == f"{provider.upper()}_API_KEY"
    assert llm.model_setting == f"{provider.upper()}_MODEL"
    assert f"{provider}-test-key" not in repr(llm)


@pytest.mark.parametrize("provider", ["openai", "groq"])
def test_only_selected_provider_credentials_are_required_in_configuration(
    isolated_llm_environment, monkeypatch, provider,
):
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv(f"{provider.upper()}_API_KEY", "selected-test-key")
    monkeypatch.setenv(f"{provider.upper()}_MODEL", "selected-test-model")

    llm = Settings().llm

    assert llm.api_key.get_secret_value() == "selected-test-key"
    assert llm.model == "selected-test-model"


@pytest.mark.parametrize("provider", ["openai", "groq"])
def test_environment_overrides_only_the_selected_provider_endpoint(
    isolated_llm_environment, monkeypatch, provider,
):
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://openai-proxy.example/v1")
    monkeypatch.setenv("GROQ_BASE_URL", "https://groq-proxy.example/openai/v1")

    settings = Settings()

    assert settings.llm.base_url == getattr(settings, f"{provider}_base_url")
    assert settings.llm.base_url.startswith(f"https://{provider}-proxy.example/")


@pytest.mark.parametrize("provider,other_provider", [
    ("openai", "groq"),
    ("groq", "openai"),
])
def test_missing_selected_credentials_do_not_fall_back_to_unused_provider(
    isolated_llm_environment, monkeypatch, provider, other_provider,
):
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv(f"{other_provider.upper()}_API_KEY", "unused-test-key")
    monkeypatch.setenv(f"{other_provider.upper()}_MODEL", "unused-test-model")

    llm = Settings().llm

    assert llm.api_key is None
    assert llm.model is None
    assert "unused-test-key" not in repr(llm)


def test_environment_rejects_unsupported_provider(isolated_llm_environment, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "unsupported-provider")

    with pytest.raises(ValidationError, match="llm_provider"):
        Settings()
