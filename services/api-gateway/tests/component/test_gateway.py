import httpx
import pytest
import respx
from fastapi.testclient import TestClient
from gateway.config import settings


@pytest.mark.asyncio
async def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_correlation_id_propagation(client: TestClient):
    # Using respx to mock the downstream call
    with respx.mock:
        respx.get(f"{settings.STORE_SERVICE_URL}/api/v1/store/offerings").mock(
            return_value=httpx.Response(200, json={"items": []})
        )

        response = client.get(
            "/api/v1/store/offerings", headers={"X-Correlation-ID": "test-id"}
        )
        assert response.status_code == 200
        assert response.headers["X-Correlation-ID"] == "test-id"


@pytest.mark.asyncio
async def test_b3_trace_headers_propagated(client: TestClient):
    """Verify B3 trace headers are forwarded to downstream services."""
    captured_headers = {}

    def capture_request(request):
        captured_headers.update(dict(request.headers))
        return httpx.Response(200, json={"items": []})

    with respx.mock:
        respx.get(f"{settings.STORE_SERVICE_URL}/api/v1/store/offerings").mock(
            side_effect=capture_request
        )

        # Send request with B3 trace headers
        response = client.get(
            "/api/v1/store/offerings",
            headers={
                "X-B3-TraceId": "463ac35c9f6413ad48485a3953bb6124",
                "X-B3-SpanId": "a2fb4a1d1a96d312",
                "X-B3-Sampled": "1",
            },
        )
        assert response.status_code == 200

        # Verify B3 headers were forwarded
        # Note: Headers may be lowercase in the captured request
        header_keys_lower = [k.lower() for k in captured_headers.keys()]
        assert any("b3" in k or "traceid" in k for k in header_keys_lower)

@pytest.mark.asyncio
async def test_correlation_id_generation(client: TestClient):
    with respx.mock:
        respx.get(f"{settings.STORE_SERVICE_URL}/api/v1/store/offerings").mock(
            return_value=httpx.Response(200, json={"items": []})
        )

        response = client.get("/api/v1/store/offerings")
        assert response.status_code == 200
        assert "X-Correlation-ID" in response.headers
        assert len(response.headers["X-Correlation-ID"]) > 0

@pytest.mark.asyncio
async def test_circuit_breaker_opens(client: TestClient):
    from gateway.main import breakers
    breaker = breakers["characteristic"]

    with respx.mock:
        # Mock consecutive failures
        route = respx.get(f"{settings.CHARACTERISTIC_SERVICE_URL}/api/v1/characteristics/123").mock(
            return_value=httpx.Response(500)
        )

        # 1st failure
        resp1 = client.get("/api/v1/characteristics/123")
        assert resp1.status_code == 500
        assert breaker.fail_count == 1

        # 2nd failure
        resp2 = client.get("/api/v1/characteristics/123")
        assert resp2.status_code == 500
        assert breaker.fail_count == 2

        # 3rd failure
        resp3 = client.get("/api/v1/characteristics/123")
        assert resp3.status_code == 500
        # After 3 failures, the breaker should transition to OPEN
        assert breaker.current_state == "open"

        # 4th call should be blocked by circuit breaker (503)
        resp4 = client.get("/api/v1/characteristics/123")
        assert resp4.status_code == 503
        assert "Circuit Open" in resp4.json()["error"]["message"]

        # Verify downstream wasn't even called for the 4th time
        assert route.call_count == 3

@pytest.mark.asyncio
async def test_gateway_timeout(client: TestClient):
    with respx.mock:
        # Mock a hanging service
        respx.get(f"{settings.PRICING_SERVICE_URL}/api/v1/prices/123").mock(
            side_effect=httpx.TimeoutException("Hanging")
        )

        response = client.get("/api/v1/prices/123")
        assert response.status_code == 504
        assert "timed out" in response.json()["error"]["message"]

@pytest.mark.asyncio
async def test_routing_to_correct_service(client: TestClient):
    with respx.mock:
        respx.get(f"{settings.IDENTITY_SERVICE_URL}/api/v1/auth/me").mock(
            return_value=httpx.Response(200, json={"user": "admin"})
        )

        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200
        assert response.json()["user"] == "admin"
