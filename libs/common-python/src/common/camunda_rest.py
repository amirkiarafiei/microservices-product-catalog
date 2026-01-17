from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BpmnError(Exception):
    """
    Raise from a task handler to trigger a BPMN error boundary event.
    """

    error_code: str
    message: str


def _parse_camunda_variables(raw: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in (raw or {}).items():
        val = v.get("value")
        # Camunda Object variables may be returned as JSON strings
        if isinstance(val, str):
            s = val.strip()
            if (s.startswith("[") and s.endswith("]")) or (s.startswith("{") and s.endswith("}")):
                try:
                    val = json.loads(s)
                except Exception:
                    pass
        out[k] = val
    return out


def _to_camunda_variables(values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert python values into Camunda variables payload for /complete.
    """
    out: Dict[str, Any] = {}
    for k, v in (values or {}).items():
        if isinstance(v, bool):
            out[k] = {"value": v, "type": "Boolean"}
        elif isinstance(v, int):
            out[k] = {"value": v, "type": "Integer"}
        elif isinstance(v, float):
            out[k] = {"value": v, "type": "Double"}
        elif isinstance(v, (list, dict)):
            out[k] = {"value": json.dumps(v), "type": "Json"}
        elif v is None:
            out[k] = {"value": None, "type": "Null"}
        else:
            out[k] = {"value": str(v), "type": "String"}
    return out


TaskHandler = Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]


class CamundaRestWorker:
    """
    Minimal Camunda External Task worker using Engine REST API.
    """

    def __init__(
        self,
        base_url: str,
        worker_id: str,
        *,
        max_tasks: int = 5,
        lock_duration_ms: int = 60_000,
        async_response_timeout_ms: int = 20_000,
        poll_interval_s: float = 0.2,
    ):
        self.base_url = base_url.rstrip("/")
        self.worker_id = worker_id
        self.max_tasks = max_tasks
        self.lock_duration_ms = lock_duration_ms
        self.async_response_timeout_ms = async_response_timeout_ms
        self.poll_interval_s = poll_interval_s
        self._topics: Dict[str, TaskHandler] = {}

    def subscribe(self, topic: str, handler: TaskHandler) -> None:
        self._topics[topic] = handler

    def run_forever(self) -> None:
        logger.info(f"CamundaRestWorker starting: {self.worker_id} (topics={list(self._topics.keys())})")
        with httpx.Client(timeout=30.0) as client:
            while True:
                try:
                    tasks = self._fetch_and_lock(client)
                    if not tasks:
                        time.sleep(self.poll_interval_s)
                        continue
                    for task in tasks:
                        self._handle_task(client, task)
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logger.error(f"Worker loop error: {e!s}")
                    time.sleep(1.0)

    def _fetch_and_lock(self, client: httpx.Client) -> list[dict]:
        payload = {
            "workerId": self.worker_id,
            "maxTasks": self.max_tasks,
            "usePriority": True,
            "asyncResponseTimeout": self.async_response_timeout_ms,
            "topics": [
                {"topicName": t, "lockDuration": self.lock_duration_ms} for t in self._topics.keys()
            ],
        }
        resp = client.post(f"{self.base_url}/external-task/fetchAndLock", json=payload)
        resp.raise_for_status()
        return resp.json()

    def _handle_task(self, client: httpx.Client, task: dict) -> None:
        task_id = task["id"]
        topic = task.get("topicName")
        handler = self._topics.get(topic)
        if not handler:
            logger.warning(f"No handler registered for topic={topic}; failing task={task_id}")
            self._fail_task(client, task_id, "No handler registered")
            return

        variables = _parse_camunda_variables(task.get("variables", {}))
        try:
            out_vars = handler(variables, task) or {}
            self._complete_task(client, task_id, out_vars)
        except BpmnError as be:
            self._bpmn_error(client, task_id, be.error_code, be.message)
        except Exception as e:
            self._fail_task(client, task_id, str(e))

    def _complete_task(self, client: httpx.Client, task_id: str, variables: Dict[str, Any]) -> None:
        payload = {"workerId": self.worker_id, "variables": _to_camunda_variables(variables)}
        resp = client.post(f"{self.base_url}/external-task/{task_id}/complete", json=payload)
        resp.raise_for_status()

    def _fail_task(self, client: httpx.Client, task_id: str, message: str) -> None:
        payload = {
            "workerId": self.worker_id,
            "errorMessage": message,
            "errorDetails": message,
            "retries": 0,
            "retryTimeout": 0,
        }
        resp = client.post(f"{self.base_url}/external-task/{task_id}/failure", json=payload)
        resp.raise_for_status()

    def _bpmn_error(self, client: httpx.Client, task_id: str, error_code: str, message: str) -> None:
        payload = {"workerId": self.worker_id, "errorCode": error_code, "errorMessage": message}
        resp = client.post(f"{self.base_url}/external-task/{task_id}/bpmnError", json=payload)
        resp.raise_for_status()

