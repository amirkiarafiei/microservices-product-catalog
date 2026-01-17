import logging
import os
from typing import Any, Dict

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


def run_offering_worker():
    identity_url = os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8001")
    token = _get_admin_token(identity_url)
    auth_headers = {"Authorization": f"Bearer {token}"}

    offering_api_url = os.getenv("OFFERING_API_URL", "http://localhost:8005")
    worker = CamundaRestWorker(base_url=settings.CAMUNDA_URL, worker_id=f"offering-worker-{settings.SERVICE_NAME}")

    def handle_confirm_publication(variables: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        offering_id = variables.get("offeringId")
        logger.info(f"Confirming publication for offering {offering_id}")

        resp = httpx.post(
            f"{offering_api_url}/api/v1/offerings/{offering_id}/confirm",
            headers=auth_headers,
            timeout=10.0,
        )
        if resp.status_code != 200:
            raise BpmnError("CONFIRM_PUBLICATION_FAILED", f"Failed to confirm offering {offering_id}: {resp.text}")
        return {}

    def handle_revert_to_draft(variables: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        offering_id = variables.get("offeringId")
        logger.info(f"Reverting offering {offering_id} to draft")

        resp = httpx.post(
            f"{offering_api_url}/api/v1/offerings/{offering_id}/fail",
            headers=auth_headers,
            timeout=10.0,
        )
        if resp.status_code != 200:
            logger.error(f"Failed to revert offering {offering_id}: {resp.text}")
        return {}

    worker.subscribe("confirm-publication", handle_confirm_publication)
    worker.subscribe("revert-offering-to-draft", handle_revert_to_draft)
    worker.run_forever()
