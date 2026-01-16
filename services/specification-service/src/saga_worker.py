import asyncio
import logging

import httpx
from camunda.external_task.external_task import ExternalTask
from common.camunda import CamundaWorker

from .config import settings

logger = logging.getLogger(__name__)

async def run_specification_worker():
    worker = CamundaWorker(base_url=settings.CAMUNDA_URL, worker_id=f"spec-worker-{settings.SERVICE_NAME}")

    def handle_validate_specs(task: ExternalTask):
        spec_ids = task.get_variable("specificationIds")

        logger.info(f"Validating specifications: {spec_ids}")

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                "http://localhost:8003/api/v1/specifications/validate",
                json=spec_ids,
                headers={"X-Internal-Token": "secret"}
            )
            if resp.status_code != 204:
                raise Exception(f"Validation failed for specifications {spec_ids}: {resp.text}")

        return {}

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: worker.subscribe("validate-specifications", handle_validate_specs))
