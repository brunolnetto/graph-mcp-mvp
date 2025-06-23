"""Tests for main application endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "status" in data
    assert "workflow_engine" in data


def test_health_endpoint(client: TestClient):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data
    assert "version" in data
    assert "engine" in data


def test_api_docs_available(client: TestClient):
    """Test that API documentation is available."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_redoc_available(client: TestClient):
    """Test that ReDoc documentation is available."""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


# Test lifespan functionality
def test_lifespan_startup():
    """Test application lifespan startup."""
    from app.main import lifespan
    from fastapi import FastAPI
    
    app = FastAPI()
    
    # Test that lifespan can be entered and exited
    async def test_lifespan():
        async with lifespan(app):
            pass
    
    # This should not raise any exceptions
    import asyncio
    asyncio.run(test_lifespan()) 