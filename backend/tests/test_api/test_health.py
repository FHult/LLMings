"""Health endpoint tests."""
import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health check endpoint returns healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test root endpoint returns API info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "LLMings API"
    assert data["status"] == "running"
    assert "configured_providers" in data
