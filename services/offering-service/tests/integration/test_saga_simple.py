import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from offering.config import settings


@pytest.fixture
def mock_httpx_client():
    # We mock the constructor of AsyncClient
    with patch("httpx.AsyncClient") as MockClientClass:
        # The instance created by the constructor
        mock_instance = MockClientClass.return_value

        # Async context manager methods
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None

        # Mock the post method to be an async function
        mock_instance.post = AsyncMock()
        mock_instance.get = AsyncMock()

        yield mock_instance

@pytest.mark.asyncio
async def test_initiate_publication_triggers_camunda_simple(client: TestClient, db_session, mock_httpx_client):
    # Setup: Configure the mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "process-123"}

    # When client.post is awaited, return the mock_response
    mock_httpx_client.post.return_value = mock_response

    spec_id = str(uuid.uuid4())
    price_id = str(uuid.uuid4())

    # Mock spec/price validation calls
    ok_get_resp = MagicMock()
    ok_get_resp.status_code = 200
    mock_httpx_client.get.return_value = ok_get_resp

    # 1. Create offering (must be publishable: >=1 spec, >=1 price, >=1 channel)
    create_resp = client.post("/api/v1/offerings", json={
        "name": "Saga Mock Test",
        "description": "Test",
        "specification_ids": [spec_id],
        "pricing_ids": [price_id],
        "sales_channels": ["WEB"]
    })
    assert create_resp.status_code == 201
    off_id = create_resp.json()["id"]

    # 2. Initiate publication
    pub_resp = client.post(f"/api/v1/offerings/{off_id}/publish")

    # Assertions
    assert pub_resp.status_code == 200

    # Verify Camunda was called
    mock_httpx_client.post.assert_called_once()

    # Check arguments
    call_args = mock_httpx_client.post.call_args
    # call_args[0] are positional args (url), call_args[1] are kwargs (json, timeout)
    url = call_args[0][0]
    kwargs = call_args[1]

    assert f"{settings.CAMUNDA_URL}/process-definition/key/offering-publication-saga/start" in url
    assert str(off_id) == kwargs["json"]["variables"]["offeringId"]["value"]

@pytest.mark.asyncio
async def test_confirm_publication_simple(client: TestClient, db_session):
    spec_id = str(uuid.uuid4())
    price_id = str(uuid.uuid4())

    with patch("httpx.AsyncClient") as MockClientClass:
        mock_instance = MockClientClass.return_value
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(return_value=MagicMock(status_code=200))
        mock_instance.post = AsyncMock(return_value=MagicMock(status_code=200, json=MagicMock(return_value={"id": "process-123"})))

        # 1. Create offering (publishable)
        create_resp = client.post("/api/v1/offerings", json={
            "name": "Confirm Mock Test",
            "specification_ids": [spec_id],
            "pricing_ids": [price_id],
            "sales_channels": ["WEB"]
        })
        off_id = create_resp.json()["id"]

        # 2. Move to PUBLISHING
        pub_resp = client.post(f"/api/v1/offerings/{off_id}/publish")
        assert pub_resp.status_code == 200

    # 3. Confirm (simulating Camunda worker)
    conf_resp = client.post(f"/api/v1/offerings/{off_id}/confirm")

    assert conf_resp.status_code == 200
    assert conf_resp.json()["lifecycle_status"] == "PUBLISHED"

@pytest.mark.asyncio
async def test_fail_publication_simple(client: TestClient, db_session):
    spec_id = str(uuid.uuid4())
    price_id = str(uuid.uuid4())

    with patch("httpx.AsyncClient") as MockClientClass:
        mock_instance = MockClientClass.return_value
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.get = AsyncMock(return_value=MagicMock(status_code=200))
        mock_instance.post = AsyncMock(return_value=MagicMock(status_code=200, json=MagicMock(return_value={"id": "process-123"})))

        # 1. Create offering (publishable)
        create_resp = client.post("/api/v1/offerings", json={
            "name": "Fail Mock Test",
            "specification_ids": [spec_id],
            "pricing_ids": [price_id],
            "sales_channels": ["WEB"]
        })
        off_id = create_resp.json()["id"]

        # 2. Move to PUBLISHING
        pub_resp = client.post(f"/api/v1/offerings/{off_id}/publish")
        assert pub_resp.status_code == 200

    # 3. Fail (simulating Camunda worker)
    fail_resp = client.post(f"/api/v1/offerings/{off_id}/fail")

    assert fail_resp.status_code == 200
    assert fail_resp.json()["lifecycle_status"] == "DRAFT"
