import httpx


def test_zero_trust_direct_access(e2e_ctx):
    """
    Verifies that microservices enforce authentication even if accessed directly,
    bypassing the API Gateway. This confirms the Zero Trust architecture.
    """

    # 1. Get Direct Service URL (bypassing Gateway)
    char_service_url = e2e_ctx.services["characteristic"]
    gateway_url = e2e_ctx.services["gateway"]

    # 2. Get Valid Token (via Gateway -> Identity)
    r = httpx.post(
        f"{gateway_url}/api/v1/auth/login",
        data={"username": "admin", "password": "admin"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]

    # 3. Attempt Direct Access WITHOUT Token
    # Should fail because service validates token independently
    r_no_auth = httpx.get(f"{char_service_url}/api/v1/characteristics")
    assert r_no_auth.status_code == 401, "Direct access without token should be unauthorized"

    # 4. Attempt Direct Access WITH Valid Token
    # Should succeed because service trusts the public key from Identity Service
    r_auth = httpx.get(
        f"{char_service_url}/api/v1/characteristics",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert r_auth.status_code == 200, "Direct access with valid token should succeed"

    # 5. Attempt Direct Access WITH Invalid Token
    r_bad_auth = httpx.get(
        f"{char_service_url}/api/v1/characteristics",
        headers={"Authorization": "Bearer invalid.token.signature"}
    )
    assert r_bad_auth.status_code == 401, "Direct access with invalid token should be unauthorized"

def test_gateway_enforces_auth(e2e_ctx):
    """
    Verifies that the Gateway also enforces authentication before forwarding.
    """
    gateway_url = e2e_ctx.services["gateway"]

    # Attempt access via Gateway without token
    r = httpx.get(f"{gateway_url}/api/v1/characteristics")
    assert r.status_code == 401

