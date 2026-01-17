import time
from typing import Callable

import httpx


def _wait_until(fn: Callable[[], bool], timeout_s: float = 60.0, interval_s: float = 1.0):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if fn():
            return
        time.sleep(interval_s)
    raise TimeoutError("Condition not met in time")


def test_happy_path_publish_and_store_visibility(e2e_ctx, start_worker):
    # Start all saga workers
    start_worker("pricing")
    start_worker("spec")
    start_worker("store")
    start_worker("offering")

    gw = e2e_ctx.services["gateway"]

    # Login (via gateway -> identity)
    r = httpx.post(
        f"{gw}/api/v1/auth/login",
        data={"username": "admin", "password": "admin"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10.0,
    )
    r.raise_for_status()
    token = r.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    # Create characteristic
    r = httpx.post(
        f"{gw}/api/v1/characteristics",
        headers=auth,
        json={"name": "Speed", "value": "100", "unit_of_measure": "Mbps"},
        timeout=10.0,
    )
    r.raise_for_status()
    char_id = r.json()["id"]

    # Create specification (retry until spec-service consumer has cached the characteristic)
    spec_id = None
    for _ in range(40):
        rr = httpx.post(
            f"{gw}/api/v1/specifications",
            headers=auth,
            json={"name": f"FiberSpec-{time.time()}", "characteristic_ids": [char_id]},
            timeout=10.0,
        )
        if rr.status_code == 201:
            spec_id = rr.json()["id"]
            break
        time.sleep(2.0)
    assert spec_id is not None

    # Create price
    r = httpx.post(
        f"{gw}/api/v1/prices",
        headers=auth,
        json={"name": "BasePrice", "value": "49.99", "unit": "per month", "currency": "USD"},
        timeout=10.0,
    )
    r.raise_for_status()
    price_id = r.json()["id"]

    # Create offering
    r = httpx.post(
        f"{gw}/api/v1/offerings",
        headers=auth,
        json={
            "name": "Fiber Bundle",
            "description": "E2E",
            "specification_ids": [spec_id],
            "pricing_ids": [price_id],
            "sales_channels": ["WEB"],
        },
        timeout=10.0,
    )
    r.raise_for_status()
    offering_id = r.json()["id"]

    # Publish (starts saga; workers should complete)
    r = httpx.post(f"{gw}/api/v1/offerings/{offering_id}/publish", headers=auth, timeout=10.0)
    r.raise_for_status()

    # Wait until offering is PUBLISHED
    def is_published():
        resp = httpx.get(f"{gw}/api/v1/offerings/{offering_id}", headers=auth, timeout=10.0)
        return resp.status_code == 200 and resp.json()["lifecycle_status"] == "PUBLISHED"

    _wait_until(is_published, timeout_s=90.0, interval_s=2.0)

    # Wait until store contains it
    def in_store():
        resp = httpx.get(f"{gw}/api/v1/store/offerings/{offering_id}", timeout=10.0)
        return resp.status_code == 200 and resp.json()["id"] == offering_id

    _wait_until(in_store, timeout_s=90.0, interval_s=2.0)

    # Retire offering (should publish event, store consumer removes it)
    r = httpx.post(f"{gw}/api/v1/offerings/{offering_id}/retire", headers=auth, timeout=10.0)
    r.raise_for_status()

    def store_removed():
        resp = httpx.get(f"{gw}/api/v1/store/offerings/{offering_id}", timeout=10.0)
        return resp.status_code == 404

    _wait_until(store_removed, timeout_s=90.0, interval_s=2.0)

