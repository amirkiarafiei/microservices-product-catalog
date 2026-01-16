"""
API Gateway - Unified Entry Point for TMF Product Catalog Microservices.

Features:
- Reverse proxy to all microservices
- Circuit breaker pattern for resilience
- Correlation ID propagation
- OpenTelemetry distributed tracing with B3 propagation
- CORS support
"""

import time
import uuid
from typing import Any, Dict

import httpx
from common.logging import setup_logging
from common.schemas import ErrorDetail, ErrorResponse
from common.tracing import (
    get_current_trace_context,
    instrument_fastapi,
    instrument_httpx,
    setup_tracing,
)
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry.propagate import inject

from .config import settings
from .resilience import AsyncCircuitBreaker, CircuitBreakerError

# Setup logging first
logger = setup_logging(settings.SERVICE_NAME, settings.LOG_LEVEL)

# Setup tracing
setup_tracing(
    service_name=settings.SERVICE_NAME,
    zipkin_endpoint=settings.ZIPKIN_ENDPOINT,
    enabled=settings.TRACING_ENABLED,
)

# Instrument HTTPX for outgoing requests
instrument_httpx()

# Circuit Breakers Registry
breakers: Dict[str, AsyncCircuitBreaker] = {
    "identity": AsyncCircuitBreaker(
        fail_max=settings.CB_FAILURE_THRESHOLD,
        reset_timeout=settings.CB_RESET_TIMEOUT,
        name="identity",
    ),
    "characteristic": AsyncCircuitBreaker(
        fail_max=settings.CB_FAILURE_THRESHOLD,
        reset_timeout=settings.CB_RESET_TIMEOUT,
        name="characteristic",
    ),
    "specification": AsyncCircuitBreaker(
        fail_max=settings.CB_FAILURE_THRESHOLD,
        reset_timeout=settings.CB_RESET_TIMEOUT,
        name="specification",
    ),
    "pricing": AsyncCircuitBreaker(
        fail_max=settings.CB_FAILURE_THRESHOLD,
        reset_timeout=settings.CB_RESET_TIMEOUT,
        name="pricing",
    ),
    "offering": AsyncCircuitBreaker(
        fail_max=settings.CB_FAILURE_THRESHOLD,
        reset_timeout=settings.CB_RESET_TIMEOUT,
        name="offering",
    ),
    "store": AsyncCircuitBreaker(
        fail_max=settings.CB_FAILURE_THRESHOLD,
        reset_timeout=settings.CB_RESET_TIMEOUT,
        name="store",
    ),
}

app = FastAPI(
    title="API Gateway",
    description="Unified Entry Point for TMF Product Catalog Microservices",
    version="0.1.0",
)

# Instrument FastAPI for tracing (excludes health endpoints)
instrument_fastapi(app, excluded_urls="health")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """
    Middleware to manage Correlation ID.

    Generates or propagates correlation ID for request tracking.
    Also attaches trace context info to response headers.
    """
    correlation_id = request.headers.get("X-Correlation-ID")
    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    # Store in request state for later use
    request.state.correlation_id = correlation_id

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Add correlation and timing to response headers
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Process-Time"] = str(process_time)

    # Add trace context to response for debugging
    trace_ctx = get_current_trace_context()
    if trace_ctx.get("trace_id"):
        response.headers["X-Trace-ID"] = trace_ctx["trace_id"]

    return response


def inject_trace_headers(headers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inject B3 trace headers into outgoing request headers.

    Args:
        headers: Existing headers dict.

    Returns:
        Headers with B3 trace context injected.
    """
    # Create a mutable copy
    carrier = dict(headers)
    inject(carrier)
    return carrier


async def proxy_request(
    service_name: str, base_url: str, path: str, request: Request
) -> Response:
    """
    Generic reverse proxy with Circuit Breaker, Timeouts, and Trace Propagation.
    """
    breaker = breakers.get(service_name)
    if not breaker:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"No circuit breaker configured for service: {service_name}"},
        )

    method = request.method
    headers = dict(request.headers)
    headers["X-Correlation-ID"] = request.state.correlation_id
    headers.pop("host", None)

    # Inject B3 trace context into headers for downstream services
    headers = inject_trace_headers(headers)

    content = await request.body()
    params = dict(request.query_params)
    url = f"{base_url}/{path}"

    async def do_request():
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(settings.READ_TIMEOUT, connect=settings.CONNECTION_TIMEOUT)
        ) as client:
            resp = await client.request(
                method=method,
                url=url,
                headers=headers,
                content=content,
                params=params,
            )

            if 500 <= resp.status_code < 600:
                raise httpx.HTTPStatusError(
                    message=f"Server error: {resp.status_code}",
                    request=resp.request,
                    response=resp,
                )
            return resp

    try:
        resp = await breaker.call(do_request)
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
        )
    except CircuitBreakerError:
        logger.error(f"Circuit open for service {service_name}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="SERVICE_UNAVAILABLE",
                    message=f"Service '{service_name}' is temporarily unavailable (Circuit Open).",
                )
            ).model_dump(),
        )
    except httpx.HTTPStatusError as e:
        return Response(
            content=e.response.content,
            status_code=e.response.status_code,
            headers=dict(e.response.headers),
        )
    except httpx.TimeoutException:
        logger.error(f"Timeout calling service {service_name}")
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="GATEWAY_TIMEOUT",
                    message=f"Service '{service_name}' timed out.",
                )
            ).model_dump(),
        )
    except Exception as e:
        logger.error(f"Error calling service {service_name}: {e!s}")
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="BAD_GATEWAY",
                    message=f"Failed to communicate with service '{service_name}'.",
                )
            ).model_dump(),
        )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.SERVICE_NAME}


@app.get("/health/dependencies")
async def health_dependencies():
    results = {}
    services = {
        "identity": settings.IDENTITY_SERVICE_URL,
        "characteristic": settings.CHARACTERISTIC_SERVICE_URL,
        "specification": settings.SPECIFICATION_SERVICE_URL,
        "pricing": settings.PRICING_SERVICE_URL,
        "offering": settings.OFFERING_SERVICE_URL,
        "store": settings.STORE_SERVICE_URL,
    }

    async with httpx.AsyncClient(timeout=2.0) as client:
        for name, url in services.items():
            try:
                resp = await client.get(f"{url}/health")
                results[name] = "healthy" if resp.status_code == 200 else "unhealthy"
            except Exception:
                results[name] = "unreachable"

    return {
        "status": "healthy" if all(v == "healthy" for v in results.values()) else "degraded",
        "dependencies": results,
        "circuit_breakers": {name: b.current_state for name, b in breakers.items()},
    }


@app.api_route(
    "/api/v1/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_identity(path: str, request: Request):
    return await proxy_request(
        "identity", settings.IDENTITY_SERVICE_URL, f"api/v1/auth/{path}", request
    )


@app.api_route(
    "/api/v1/characteristics/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def proxy_characteristic(path: str, request: Request):
    return await proxy_request(
        "characteristic",
        settings.CHARACTERISTIC_SERVICE_URL,
        f"api/v1/characteristics/{path}",
        request,
    )


@app.api_route(
    "/api/v1/specifications/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def proxy_specification(path: str, request: Request):
    return await proxy_request(
        "specification",
        settings.SPECIFICATION_SERVICE_URL,
        f"api/v1/specifications/{path}",
        request,
    )


@app.api_route(
    "/api/v1/prices/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_pricing(path: str, request: Request):
    return await proxy_request(
        "pricing", settings.PRICING_SERVICE_URL, f"api/v1/prices/{path}", request
    )


@app.api_route(
    "/api/v1/offerings/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_offering(path: str, request: Request):
    return await proxy_request(
        "offering", settings.OFFERING_SERVICE_URL, f"api/v1/offerings/{path}", request
    )


@app.api_route(
    "/api/v1/store/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_store(path: str, request: Request):
    return await proxy_request(
        "store", settings.STORE_SERVICE_URL, f"api/v1/store/{path}", request
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
