import logging
from typing import Any, Dict

import httpx
from common.camunda_rest import BpmnError, CamundaRestWorker

from .config import settings

logger = logging.getLogger(__name__)


def run_store_worker():
    store_api_url = os.getenv("STORE_API_URL", "http://localhost:8006")
    worker = CamundaRestWorker(base_url=settings.CAMUNDA_URL, worker_id=f"store-worker-{settings.SERVICE_NAME}")

    def handle_create_store_entry(variables: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        offering_id = variables.get("offeringId")
        logger.info(f"Creating store entry for offering {offering_id}")

        resp = httpx.post(f"{store_api_url}/api/v1/store/sync/{offering_id}", timeout=30.0)
        if resp.status_code != 204:
            raise BpmnError("CREATE_STORE_FAILED", f"Failed to sync store for offering {offering_id}: {resp.text}")
        return {}

    def handle_delete_store_entry(variables: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        offering_id = variables.get("offeringId")
        logger.info(f"Deleting store entry for offering {offering_id}")

        resp = httpx.delete(f"{store_api_url}/api/v1/store/offerings/{offering_id}", timeout=10.0)
        if resp.status_code != 204:
            logger.error(f"Failed to delete store entry {offering_id}: {resp.text}")
        return {}

    worker.subscribe("create-store-entry", handle_create_store_entry)
    worker.subscribe("delete-store-entry", handle_delete_store_entry)
    worker.run_forever()
