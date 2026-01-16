import asyncio
import logging
import time
from enum import Enum
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half-open"

class AsyncCircuitBreaker:
    def __init__(self, fail_max: int, reset_timeout: float, name: str):
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self.name = name
        self.state = CircuitState.CLOSED
        self.fail_count = 0
        self.last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()

    @property
    def current_state(self) -> str:
        return self.state.value

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        async with self._lock:
            await self._before_call()

        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                await self._on_success()
            return result
        except Exception as e:
            async with self._lock:
                await self._on_failure(e)
            raise e

    async def _before_call(self):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.reset_timeout:
                logger.info(f"Circuit {self.name} transitioning to HALF-OPEN")
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerError(f"Circuit {self.name} is OPEN")
        
    async def _on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit {self.name} transitioning to CLOSED")
            self.state = CircuitState.CLOSED
            self.fail_count = 0
        elif self.state == CircuitState.CLOSED:
            self.fail_count = 0

    async def _on_failure(self, e: Exception):
        self.fail_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN or self.fail_count >= self.fail_max:
            if self.state != CircuitState.OPEN:
                logger.error(f"Circuit {self.name} transitioning to OPEN due to: {str(e)}")
            self.state = CircuitState.OPEN

class CircuitBreakerError(Exception):
    pass
