def test_health_check_api(client):
    response = client.get("/health")
    assert response.status_code == 200
