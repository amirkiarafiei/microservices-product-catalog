from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@patch("store.main.mongodb_client")
def test_get_offering_not_found(mock_mongo, client: TestClient):
    mock_mongo.offerings.find_one = AsyncMock(return_value=None)

    response = client.get("/api/v1/store/offerings/non-existent")
    assert response.status_code == 404
    assert response.json()["error"] == "Offering not found"

@patch("store.main.mongodb_client")
def test_get_offering_success(mock_mongo, client: TestClient):
    mock_offering = {"id": "off-123", "name": "Test Offering"}
    mock_mongo.offerings.find_one = AsyncMock(return_value=mock_offering)

    response = client.get("/api/v1/store/offerings/off-123")
    assert response.status_code == 200
    assert response.json()["id"] == "off-123"
    assert response.json()["name"] == "Test Offering"

@patch("store.main.es_client")
def test_search_offerings_error(mock_es, client: TestClient):
    mock_es.search_offerings = AsyncMock(side_effect=Exception("ES down"))

    response = client.get("/api/v1/store/search?q=test")
    assert response.status_code == 500
    assert response.json()["error"] == "Search failed"
