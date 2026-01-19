import logging
from typing import Any, Callable, Dict

from camunda.external_task.external_task import ExternalTask
from camunda.external_task.external_task_worker import ExternalTaskWorker

logger = logging.getLogger(__name__)

class CamundaWorker:
    def __init__(self, base_url: str, worker_id: str = "python-worker"):
        self.base_url = base_url
        self.worker_id = worker_id
        self.worker = ExternalTaskWorker(worker_id=worker_id, base_url=base_url)

    def subscribe(self, topic: str, handler: Callable[[ExternalTask], Dict[str, Any]]):
        """
        Subscribes to a topic and handles tasks.
        The handler should return a dict of variables to update, or None.
        If the handler raises an exception, the task will be failed.
        """
        def wrapped_handler(task: ExternalTask):
            logger.info(f"Received task {task.get_task_id()} for topic {topic}")
            try:
                variables = handler(task)
                logger.info(f"Task {task.get_task_id()} completed successfully")
                return task.complete(global_variables=variables)
            except Exception as e:
                logger.error(f"Task {task.get_task_id()} failed: {str(e)}")
                # For simplicity, we fail with a generic error code.
                # In a real system, we'd handle retries vs permanent failures.
                return task.failure(
                    error_message=str(e),
                    error_details=str(e),
                    retries=0,
                    retry_timeout=0
                )

        logger.info(f"Subscribing to topic: {topic}")
        # Note: self.worker.subscribe is blocking in some versions or requires a loop.
        # This implementation depends on the library specifics.
        self.worker.subscribe(topic, wrapped_handler)
