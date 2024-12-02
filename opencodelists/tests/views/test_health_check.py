def test_health_check_successful(client):
    response = client.get("/health-check/")
    assert response.status_code == 200
