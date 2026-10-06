import pytest
from sqlalchemy.engine import make_url

pytest.importorskip("pydantic_settings")

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
