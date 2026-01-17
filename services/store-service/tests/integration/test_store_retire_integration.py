import asyncio


def test_retire_offering_deletes_from_mongo_and_es(client, mongodb_client, es_client):
    offering_id = "off-retire-1"
    doc = {"id": offering_id, "name": "To Retire", "pricing": [], "specifications": []}

    asyncio.run(mongodb_client.offerings.replace_one({"id": offering_id}, doc, upsert=True))
    asyncio.run(es_client.index_offering(offering_id, doc))

    # delete endpoint triggers retire_offering
    resp = client.delete(f"/api/v1/store/offerings/{offering_id}")
    assert resp.status_code == 204

    stored = asyncio.run(mongodb_client.offerings.find_one({"id": offering_id}))
    assert stored is None

    es_res = asyncio.run(es_client.search_offerings({"query": {"match_all": {}}}, from_=0, size=50))
    hits = es_res["hits"]["hits"]
    assert all(h["_id"] != offering_id for h in hits)

