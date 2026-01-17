import pytest


@pytest.mark.asyncio
async def test_retire_offering_deletes_from_mongo_and_es(async_client, mongodb_client, es_client):
    client = async_client
    offering_id = "off-retire-1"
    doc = {"id": offering_id, "name": "To Retire", "pricing": [], "specifications": []}

    await mongodb_client.offerings.replace_one({"id": offering_id}, doc, upsert=True)
    await es_client.index_offering(offering_id, doc)

    # delete endpoint triggers retire_offering
    resp = await client.delete(f"/api/v1/store/offerings/{offering_id}")
    assert resp.status_code == 204

    stored = await mongodb_client.offerings.find_one({"id": offering_id})
    assert stored is None

    es_res = await es_client.search_offerings({"query": {"match_all": {}}}, from_=0, size=50)
    hits = es_res["hits"]["hits"]
    assert all(h["_id"] != offering_id for h in hits)

