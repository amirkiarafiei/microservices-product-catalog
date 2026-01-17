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


def run_specification_worker():
    identity_url = os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8001")
    token = _get_admin_token(identity_url)
    auth_headers = {"Authorization": f"Bearer {token}"}

    spec_api_url = os.getenv("SPECIFICATION_API_URL", "http://localhost:8003")
    worker = CamundaRestWorker(base_url=settings.CAMUNDA_URL, worker_id=f"spec-worker-{settings.SERVICE_NAME}")

    def handle_validate_specs(variables: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        spec_ids = _as_str_list(variables.get("specificationIds"))
        logger.info(f"Validating specifications: {spec_ids}")

        resp = httpx.post(
            f"{spec_api_url}/api/v1/specifications/validate",
            json=spec_ids,
            headers=auth_headers,
            timeout=10.0,
        )
        if resp.status_code != 204:
            raise BpmnError("VALIDATE_SPECS_FAILED", f"Validation failed for specifications {spec_ids}: {resp.text}")
        return {}

    worker.subscribe("validate-specifications", handle_validate_specs)
    worker.run_forever()
