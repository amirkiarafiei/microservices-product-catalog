import uuid
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


@patch("offering.application.service.httpx.AsyncClient.get")
def test_create_offering_success(mock_get, client: TestClient):
    # Mock validation responses
    mock_get.return_value = AsyncMock(status_code=200)

    spec_id = uuid.uuid4()
    price_id = uuid.uuid4()

    offering_data = {
        "name": "Super Bundle",
        "description": "A great bundle",
        "specification_ids": [str(spec_id)],
        "pricing_ids": [str(price_id)],
        "sales_channels": ["WEB", "APP"]
    }

    response = client.post("/api/v1/offerings", json=offering_data)
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Super Bundle"
    assert created["lifecycle_status"] == "DRAFT"
    assert len(created["specification_ids"]) == 1


@patch("offering.application.service.httpx.AsyncClient.get")
def test_create_offering_invalid_ids(mock_get, client: TestClient):
    # Mock validation response failure
    mock_get.return_value = AsyncMock(status_code=404)

    offering_data = {
        "name": "Invalid Bundle",
        "specification_ids": [str(uuid.uuid4())],
        "pricing_ids": [],
        "sales_channels": []
    }

    response = client.post("/api/v1/offerings", json=offering_data)
    assert response.status_code == 400
    assert "not found or invalid" in response.json()["error"]["message"]


def test_publish_offering_flow(client: TestClient):
    # 1. Create a draft with requirements
    offering_data = {
        "name": "Publishable Offering",
        "specification_ids": [str(uuid.uuid4())],
        "pricing_ids": [str(uuid.uuid4())],
        "sales_channels": ["WEB"]
    }
    # Skip external validation for simplicity in this test by using a service that doesn't check
    # or just patch it
    with (
        patch("offering.application.service.OfferingService._validate_external_ids", new_callable=AsyncMock),
        patch("offering.application.service.httpx.AsyncClient.post", new_callable=AsyncMock) as mock_camunda_post,
    ):
        mock_camunda_post.return_value = AsyncMock(status_code=200)
        resp = client.post("/api/v1/offerings", json=offering_data)
        offering_id = resp.json()["id"]

        # 2. Publish
        publish_resp = client.post(f"/api/v1/offerings/{offering_id}/publish")
        assert publish_resp.status_code == 200
        publishing = publish_resp.json()
        # Phase 12: publish starts the saga, leaving the offering in PUBLISHING until confirmed
        assert publishing["lifecycle_status"] == "PUBLISHING"

        # 3. Confirm (simulating Camunda worker)
        confirm_resp = client.post(f"/api/v1/offerings/{offering_id}/confirm")
        assert confirm_resp.status_code == 200
        confirmed = confirm_resp.json()
        assert confirmed["lifecycle_status"] == "PUBLISHED"
        assert confirmed["published_at"] is not None


def test_update_restricted_to_draft(client: TestClient):
    with (
        patch("offering.application.service.OfferingService._validate_external_ids", new_callable=AsyncMock),
        patch("offering.application.service.httpx.AsyncClient.post", new_callable=AsyncMock) as mock_camunda_post,
    ):
        mock_camunda_post.return_value = AsyncMock(status_code=200)
        # Create and publish
        offering_data = {
            "name": "Locked Offering",
            "specification_ids": [str(uuid.uuid4())],
            "pricing_ids": [str(uuid.uuid4())],
            "sales_channels": ["WEB"]
        }
        resp = client.post("/api/v1/offerings", json=offering_data)
        offering_id = resp.json()["id"]
        client.post(f"/api/v1/offerings/{offering_id}/publish")
        client.post(f"/api/v1/offerings/{offering_id}/confirm")

        # Try to update
        update_data = {"name": "New Name", "specification_ids": [], "pricing_ids": [], "sales_channels": []}
        update_resp = client.put(f"/api/v1/offerings/{offering_id}", json=update_data)
        assert update_resp.status_code == 400
        assert "Cannot update offering in PUBLISHED state" in update_resp.json()["error"]["message"]
