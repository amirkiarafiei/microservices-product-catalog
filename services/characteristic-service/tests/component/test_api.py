from fastapi import status


def test_create_characteristic_api(client):
    response = client.post(
        "/api/v1/characteristics",
        json={
            "name": "API Speed",
            "value": "100",
            "unit_of_measure": "Mbps"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "API Speed"
    assert "id" in data

def test_get_characteristic_api(client):
    # Create one first
    create_res = client.post(
        "/api/v1/characteristics",
        json={"name": "To Get", "value": "1", "unit_of_measure": "GB"}
    )
    char_id = create_res.json()["id"]

    # Get it
    response = client.get(f"/api/v1/characteristics/{char_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "To Get"

def test_list_characteristics_api(client):
    client.post("/api/v1/characteristics", json={"name": "C1", "value": "1", "unit_of_measure": "GB"})
    client.post("/api/v1/characteristics", json={"name": "C2", "value": "2", "unit_of_measure": "GB"})

    response = client.get("/api/v1/characteristics")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) >= 2

def test_update_characteristic_api(client):
    create_res = client.post(
        "/api/v1/characteristics",
        json={"name": "To Update", "value": "1", "unit_of_measure": "GB"}
    )
    char_id = create_res.json()["id"]

    response = client.put(
        f"/api/v1/characteristics/{char_id}",
        json={"name": "Updated API", "value": "10"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Updated API"
    assert response.json()["value"] == "10"

def test_delete_characteristic_api(client):
    create_res = client.post(
        "/api/v1/characteristics",
        json={"name": "To Delete", "value": "1", "unit_of_measure": "GB"}
    )
    char_id = create_res.json()["id"]

    response = client.delete(f"/api/v1/characteristics/{char_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it's gone
    get_res = client.get(f"/api/v1/characteristics/{char_id}")
    assert get_res.status_code == status.HTTP_404_NOT_FOUND

def test_health_check_api(client):
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy", "service": "characteristic-service"}
