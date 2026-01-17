from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_sync_offering_writes_mongo_and_es(async_client, mongodb_client, es_client):
    client = async_client
    offering_id = "off-123"

    # Mock upstream HTTP calls done by StoreService.fetch_offering_details
    async def _mock_get(url, *args, **kwargs):
        resp = MagicMock()
        resp.status_code = 200

        if "/offerings/" in url:
            resp.json.return_value = {
                "id": offering_id,
                "name": "Test Offering",
                "description": "Desc",
                "lifecycle_status": "PUBLISHED",
                "published_at": None,
                "sales_channels": ["WEB"],
                "specification_ids": ["spec-1"],
                "pricing_ids": ["price-1"],
            }
        elif "/specifications/" in url:
            resp.json.return_value = {"id": "spec-1", "name": "Spec", "characteristic_ids": ["char-1"]}
        elif "/characteristics/" in url:
            resp.json.return_value = {
                "id": "char-1",
                "name": "Speed",
                "value": "100",
                "unit_of_measure": "Mbps",
            }
        elif "/prices/" in url:
            resp.json.return_value = {"id": "price-1", "name": "P1", "value": "49.99", "currency": "USD", "unit": "per month"}
        else:
            resp.status_code = 404
            resp.json.return_value = {}
        return resp

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = _mock_get

        resp = await client.post(f"/api/v1/store/sync/{offering_id}")
        assert resp.status_code == 204

    doc = await mongodb_client.offerings.find_one({"id": offering_id}, {"_id": 0})
    assert doc is not None
    assert doc["name"] == "Test Offering"
    assert doc["specifications"][0]["characteristics"][0]["name"] == "Speed"

    # ES should now contain the document as well
    es_res = await es_client.search_offerings({"query": {"match_all": {}}}, from_=0, size=10)
    hits = es_res["hits"]["hits"]
    assert any(h["_id"] == offering_id for h in hits)


@pytest.mark.asyncio
async def test_search_endpoint_returns_hits(async_client):
    resp = await async_client.get("/api/v1/store/search")
    assert resp.status_code == 200
    body = resp.json()
    assert "hits" in body

