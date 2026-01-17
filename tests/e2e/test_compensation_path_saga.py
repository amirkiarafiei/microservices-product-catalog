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


def test_compensation_unlocks_and_reverts(e2e_ctx, start_worker):
    # Start workers except spec (we want to delete spec before validation)
    start_worker("pricing")
    start_worker("store")
    start_worker("offering")

    gw = e2e_ctx.services["gateway"]

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
        json={"name": "Speed2", "value": "200", "unit_of_measure": "Mbps"},
        timeout=10.0,
    )
    r.raise_for_status()
    char_id = r.json()["id"]

    # Create spec (retry until cached)
    spec_id = None
    for _ in range(40):
        rr = httpx.post(
            f"{gw}/api/v1/specifications",
            headers=auth,
            json={"name": f"SpecToDelete-{time.time()}", "characteristic_ids": [char_id]},
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
        json={"name": f"PriceToUnlock-{time.time()}", "value": "19.99", "unit": "per month", "currency": "USD"},
        timeout=10.0,
    )
    r.raise_for_status()
    price_id = r.json()["id"]

    # Create offering
    r = httpx.post(
        f"{gw}/api/v1/offerings",
        headers=auth,
        json={
            "name": f"OfferToFail-{time.time()}",
            "specification_ids": [spec_id],
            "pricing_ids": [price_id],
            "sales_channels": ["WEB"],
        },
        timeout=10.0,
    )
    r.raise_for_status()
    offering_id = r.json()["id"]

    # Publish: process will lock prices then wait at validate-specifications
    r = httpx.post(f"{gw}/api/v1/offerings/{offering_id}/publish", headers=auth, timeout=10.0)
    r.raise_for_status()

    # Wait until offering is PUBLISHING (initial transition)
    _wait_until(
        lambda: httpx.get(f"{gw}/api/v1/offerings/{offering_id}", headers=auth, timeout=10.0).json().get("lifecycle_status")
        == "PUBLISHING",
        timeout_s=30.0,
        interval_s=1.0,
    )

    # Delete the specification so validate step fails
    r = httpx.delete(f"{gw}/api/v1/specifications/{spec_id}", headers=auth, timeout=10.0)
    assert r.status_code in (204, 200)

    # Now start spec worker so it picks up validate task and triggers compensation
    start_worker("spec")

    # Offering should revert back to DRAFT
    def is_draft():
        resp = httpx.get(f"{gw}/api/v1/offerings/{offering_id}", headers=auth, timeout=10.0)
        return resp.status_code == 200 and resp.json()["lifecycle_status"] == "DRAFT"

    _wait_until(is_draft, timeout_s=90.0, interval_s=2.0)

    # Price should be unlocked
    def price_unlocked():
        resp = httpx.get(f"{gw}/api/v1/prices/{price_id}", headers=auth, timeout=10.0)
        return resp.status_code == 200 and resp.json().get("locked") is False

    _wait_until(price_unlocked, timeout_s=60.0, interval_s=2.0)

