import asyncio
import logging

import httpx
from camunda.external_task.external_task import ExternalTask
from common.camunda import CamundaWorker

from .config import settings

logger = logging.getLogger(__name__)

async def run_pricing_worker():
    """
    Runs the Camunda external task worker for Pricing Service.
    """
    worker = CamundaWorker(base_url=settings.CAMUNDA_URL, worker_id=f"pricing-worker-{settings.SERVICE_NAME}")

    def handle_lock_prices(task: ExternalTask):
        offering_id = task.get_variable("offeringId")
        price_ids = task.get_variable("pricingIds")

        logger.info(f"Locking prices for offering {offering_id}: {price_ids}")

        with httpx.Client(timeout=10.0) as client:
            for price_id in price_ids:
                resp = client.post(
                    f"http://localhost:8004/api/v1/prices/{price_id}/lock",
                    json={"saga_id": str(task.get_process_instance_id())},
                    headers={"X-Internal-Token": "secret"} # Placeholder for internal auth
                )
                if resp.status_code != 200:
                    raise Exception(f"Failed to lock price {price_id}: {resp.text}")

        return {}

    def handle_unlock_prices(task: ExternalTask):
        price_ids = task.get_variable("pricingIds")

        logger.info(f"Unlocking prices: {price_ids}")

        with httpx.Client(timeout=10.0) as client:
            for price_id in price_ids:
                resp = client.post(
                    f"http://localhost:8004/api/v1/prices/{price_id}/unlock",
                    headers={"X-Internal-Token": "secret"}
                )
                # We don't fail unlocking as it's a compensation
                if resp.status_code != 200:
                    logger.error(f"Failed to unlock price {price_id}: {resp.text}")

        return {}

    # Subscribe to topics
    # Note: CamundaWorker.subscribe is blocking, so we run it in a thread
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: worker.subscribe("lock-prices", handle_lock_prices))
    await loop.run_in_executor(None, lambda: worker.subscribe("unlock-prices", handle_unlock_prices))
