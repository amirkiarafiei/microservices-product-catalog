import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_create_and_get_price(client: TestClient, db_session: Session):
    price_data = {
        "name": "Component Test Price",
        "value": "49.99",
        "unit": "per month",
        "currency": "USD"
    }
    response = client.post("/api/v1/prices", json=price_data)
    assert response.status_code == 201
    created_price = response.json()
    assert created_price["name"] == "Component Test Price"
    assert created_price["value"] == "49.99"

    response = client.get(f"/api/v1/prices/{created_price['id']}")
    assert response.status_code == 200
    fetched_price = response.json()
    assert fetched_price["name"] == "Component Test Price"


def test_lock_and_update_price(client: TestClient, db_session: Session):
    # 1. Create a price
    price_data = {
        "name": "Lock Test Price",
        "value": "10.00",
        "unit": "once",
        "currency": "EUR"
    }
    post_response = client.post("/api/v1/prices", json=price_data)
    price_id = post_response.json()["id"]

    # 2. Lock it
    saga_id = str(uuid.uuid4())
    lock_response = client.post(f"/api/v1/prices/{price_id}/lock", json={"saga_id": saga_id})
    assert lock_response.status_code == 200
    assert lock_response.json()["locked"] is True

    # 3. Try to update it - should fail
    update_data = {
        "name": "Updated Name",
        "value": "20.00",
        "unit": "once",
        "currency": "EUR"
    }
    update_response = client.put(f"/api/v1/prices/{price_id}", json=update_data)
    assert update_response.status_code == 423
    assert update_response.json()["error"]["code"] == "LOCKED"

    # 4. Unlock it
    unlock_response = client.post(f"/api/v1/prices/{price_id}/unlock")
    assert unlock_response.status_code == 200
    assert unlock_response.json()["locked"] is False

    # 5. Update again - should succeed
    update_response = client.put(f"/api/v1/prices/{price_id}", json=update_data)
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated Name"
