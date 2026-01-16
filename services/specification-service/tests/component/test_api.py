import uuid


def test_create_and_get_specification(client, db_session):
    # 1. Setup cache
    char_id = uuid.uuid4()
    # Since we use direct DB in tests, we can manually insert to cache
    from src.infrastructure.models import CachedCharacteristicORM
    db_session.add(CachedCharacteristicORM(id=char_id, name="Test Char"))
    db_session.commit()

    # 2. Create Spec
    spec_data = {
        "name": "Component Test Spec",
        "characteristic_ids": [str(char_id)]
    }
    response = client.post("/api/v1/specifications", json=spec_data)
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Component Test Spec"

    # 3. Get Spec
    spec_id = created["id"]
    response = client.get(f"/api/v1/specifications/{spec_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Component Test Spec"

def test_create_specification_invalid_char(client):
    spec_data = {
        "name": "Invalid Spec",
        "characteristic_ids": [str(uuid.uuid4())]
    }
    response = client.post("/api/v1/specifications", json=spec_data)
    assert response.status_code == 400
    assert "Missing characteristic IDs" in response.json()["error"]["message"]
