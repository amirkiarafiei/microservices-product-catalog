import asyncio
import logging

import httpx
from camunda.external_task.external_task import ExternalTask
from common.camunda import CamundaWorker

from .config import settings

logger = logging.getLogger(__name__)

async def run_store_worker():
    worker = CamundaWorker(base_url=settings.CAMUNDA_URL, worker_id=f"store-worker-{settings.SERVICE_NAME}")

    def handle_create_store_entry(task: ExternalTask):
        offering_id = task.get_variable("offeringId")

        logger.info(f"Creating store entry for offering {offering_id}")

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"http://localhost:8006/api/v1/store/sync/{offering_id}",
                headers={"X-Internal-Token": "secret"}
            )
            if resp.status_code != 204:
                raise Exception(f"Failed to sync store for offering {offering_id}: {resp.text}")

        return {}

    def handle_delete_store_entry(task: ExternalTask):
        offering_id = task.get_variable("offeringId")

        logger.info(f"Deleting store entry for offering {offering_id}")

        with httpx.Client(timeout=10.0) as client:
            resp = client.delete(
                f"http://localhost:8006/api/v1/store/offerings/{offering_id}",
                headers={"X-Internal-Token": "secret"}
            )
            if resp.status_code != 204:
                logger.error(f"Failed to delete store entry {offering_id}: {resp.text}")

        return {}

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: worker.subscribe("create-store-entry", handle_create_store_entry))
    await loop.run_in_executor(None, lambda: worker.subscribe("delete-store-entry", handle_delete_store_entry))
