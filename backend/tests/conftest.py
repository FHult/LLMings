"""Pytest configuration and fixtures."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db():
    """Create a test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncTestSession = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncTestSession() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db):
    """Create a test client with database override."""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_council_members():
    """Sample council member configuration for tests."""
    return [
        {
            "id": "member-1",
            "provider": "openai",
            "model": "gpt-4",
            "role": "Analyst",
            "archetype": "analytical",
            "is_chair": True,
        },
        {
            "id": "member-2",
            "provider": "anthropic",
            "model": "claude-3-sonnet",
            "role": "Creative",
            "archetype": "creative",
            "is_chair": False,
        },
    ]


@pytest.fixture
def sample_session_config(sample_council_members):
    """Sample session configuration for tests."""
    return {
        "prompt": "What are the benefits of test-driven development?",
        "council_members": sample_council_members,
        "iterations": 2,
        "template": "balanced",
        "preset": "balanced",
        "autopilot": True,
    }
