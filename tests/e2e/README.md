# E2E Tests

These tests verify the end-to-end functionality of the Microservices Product Catalog.
They use `testcontainers-python` to spin up a complete environment including:
- PostgreSQL
- RabbitMQ
- MongoDB
- Elasticsearch
- Camunda
- All 7 Microservices

## Prerequisites

- **Docker** must be installed and running.
- Network ports 8000-8006, 5432, 5672, 27017, 9200, 8085 must be available (or dynamically assigned by testcontainers).

## Running Tests

To run the complete E2E suite:

```bash
make test-e2e
```

Or using `uv` directly:

```bash
uv run pytest tests/e2e
```

## Test Files

- `test_happy_path_saga.py`: Full lifecycle test (Create -> Publish -> Store -> Retire).
- `test_compensation_path_saga.py`: Tests failure scenarios and rollback logic.
- `test_api_contracts.py`: Basic validation of API responses against OpenAPI specs.
- `test_advanced_contracts.py`: Strict validation of API responses, including pagination and types.
- `test_service_security.py`: Verifies Zero Trust and Gateway enforcement.

## Environment Variables

The `conftest.py` automatically handles all configuration, overriding database URLs and service endpoints to point to the temporary containers and processes started for the test session.
