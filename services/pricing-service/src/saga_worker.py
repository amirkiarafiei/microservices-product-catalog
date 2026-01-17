import logging
import os
from typing import Any, Dict, List

import httpx
from common.camunda_rest import BpmnError, CamundaRestWorker

from .config import settings

logger = logging.getLogger(__name__)


def _get_admin_token(identity_url: str) -> str:
    resp = httpx.post(
        f"{identity_url}/api/v1/auth/login",
        data={"username": "admin", "password": "admin"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10.0,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _as_str_list(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v]
    return [str(v)]


def run_pricing_worker():
    """
    Runs Pricing external task worker (lock-prices / unlock-prices) using Camunda REST API.
    """
    identity_url = os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8001")
    token = _get_admin_token(identity_url)
    auth_headers = {"Authorization": f"Bearer {token}"}

    pricing_api_url = os.getenv("PRICING_API_URL", "http://localhost:8004")
    worker = CamundaRestWorker(base_url=settings.CAMUNDA_URL, worker_id=f"pricing-worker-{settings.SERVICE_NAME}")

    def handle_lock_prices(variables: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        offering_id = variables.get("offeringId")
        price_ids = _as_str_list(variables.get("pricingIds"))
        saga_id = task.get("processInstanceId")
        logger.info(f"Locking prices for offering {offering_id}: {price_ids}")

        for price_id in price_ids:
            resp = httpx.post(
                f"{pricing_api_url}/api/v1/prices/{price_id}/lock",
                json={"saga_id": str(saga_id)},
                headers=auth_headers,
                timeout=10.0,
            )
            if resp.status_code != 200:
                raise BpmnError("LOCK_PRICES_FAILED", f"Failed to lock price {price_id}: {resp.text}")
        return {}

    def handle_unlock_prices(variables: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        price_ids = _as_str_list(variables.get("pricingIds"))
        logger.info(f"Unlocking prices: {price_ids}")
        for price_id in price_ids:
            resp = httpx.post(
                f"{pricing_api_url}/api/v1/prices/{price_id}/unlock",
                headers=auth_headers,
                timeout=10.0,
            )
            if resp.status_code != 200:
                logger.error(f"Failed to unlock price {price_id}: {resp.text}")
        return {}

    worker.subscribe("lock-prices", handle_lock_prices)
    worker.subscribe("unlock-prices", handle_unlock_prices)
    worker.run_forever()
