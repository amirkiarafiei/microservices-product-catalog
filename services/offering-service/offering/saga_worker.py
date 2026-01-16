import asyncio
import logging

import httpx
from camunda.external_task.external_task import ExternalTask
from common.camunda import CamundaWorker

from .config import settings

logger = logging.getLogger(__name__)

async def run_offering_worker():
    worker = CamundaWorker(base_url=settings.CAMUNDA_URL, worker_id=f"offering-worker-{settings.SERVICE_NAME}")

    def handle_confirm_publication(task: ExternalTask):
        offering_id = task.get_variable("offeringId")

        logger.info(f"Confirming publication for offering {offering_id}")

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"http://localhost:8005/api/v1/offerings/{offering_id}/confirm",
                headers={"X-Internal-Token": "secret"}
            )
            if resp.status_code != 200:
                raise Exception(f"Failed to confirm offering {offering_id}: {resp.text}")

        return {}

    def handle_revert_to_draft(task: ExternalTask):
        offering_id = task.get_variable("offeringId")

        logger.info(f"Reverting offering {offering_id} to draft")

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"http://localhost:8005/api/v1/offerings/{offering_id}/fail",
                headers={"X-Internal-Token": "secret"}
            )
            if resp.status_code != 200:
                logger.error(f"Failed to revert offering {offering_id}: {resp.text}")

        return {}

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: worker.subscribe("confirm-publication", handle_confirm_publication))
    await loop.run_in_executor(None, lambda: worker.subscribe("revert-offering-to-draft", handle_revert_to_draft))
