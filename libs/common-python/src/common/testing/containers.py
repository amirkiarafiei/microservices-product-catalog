from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional

import httpx


def _require_testcontainers():
    # Lazy import so runtime code paths don’t explode if a service imports common-python
    # but never uses testing helpers.
    try:
        import testcontainers  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "testcontainers is required for integration/E2E tests. "
            "Install dev deps for the target service (uv sync) or ensure testcontainers is available."
        ) from e


def wait_for_http_ok(url: str, timeout_s: float = 60.0, interval_s: float = 0.5) -> None:
    """
    Poll an HTTP endpoint until it returns 2xx/3xx.
    """
    deadline = time.time() + timeout_s
    last_err: Optional[Exception] = None
    while time.time() < deadline:
        try:
            r = httpx.get(url, timeout=5.0)
            if 200 <= r.status_code < 400:
                return
        except Exception as e:
            last_err = e
        time.sleep(interval_s)
    raise TimeoutError(f"Timed out waiting for {url} to become ready. Last error: {last_err}")


@dataclass(frozen=True)
class PostgresInfo:
    url: str  # SQLAlchemy URL (postgresql://...)
    host: str
    port: int
    username: str
    password: str
    dbname: str


@dataclass(frozen=True)
class RabbitMQInfo:
    amqp_url: str  # amqp://...
    host: str
    port: int
    username: str
    password: str


@dataclass(frozen=True)
class MongoInfo:
    url: str  # mongodb://...
    host: str
    port: int


@dataclass(frozen=True)
class ElasticsearchInfo:
    url: str  # http://...
    host: str
    port: int


@dataclass(frozen=True)
class CamundaInfo:
    url: str  # http://.../engine-rest
    host: str
    port: int


def start_postgres(dbname: str = "test_db"):
    """
    Starts a Postgres container and returns (container, PostgresInfo).
    """
    _require_testcontainers()
    from testcontainers.postgres import PostgresContainer

    image = os.getenv("TESTCONTAINERS_POSTGRES_IMAGE", "postgres:15-alpine")
    container = PostgresContainer(image=image, dbname=dbname, user="user", password="password")
    container.start()

    url = container.get_connection_url()
    host = container.get_container_host_ip()
    port = int(container.get_exposed_port(container.port_to_expose))
    return container, PostgresInfo(
        url=url,
        host=host,
        port=port,
        username="user",
        password="password",
        dbname=dbname,
    )


def start_rabbitmq(username: str = "guest", password: str = "guest"):
    """
    Starts RabbitMQ management image and returns (container, RabbitMQInfo).
    """
    _require_testcontainers()
    from testcontainers.core.container import DockerContainer

    image = os.getenv("TESTCONTAINERS_RABBITMQ_IMAGE", "rabbitmq:3.12-management-alpine")
    container = (
        DockerContainer(image)
        .with_env("RABBITMQ_DEFAULT_USER", username)
        .with_env("RABBITMQ_DEFAULT_PASS", password)
        .with_exposed_ports(5672, 15672)
    )
    container.start()

    host = container.get_container_host_ip()
    port = int(container.get_exposed_port(5672))
    return container, RabbitMQInfo(
        amqp_url=f"amqp://{username}:{password}@{host}:{port}",
        host=host,
        port=port,
        username=username,
        password=password,
    )


def start_mongodb():
    _require_testcontainers()
    from testcontainers.mongodb import MongoDbContainer

    image = os.getenv("TESTCONTAINERS_MONGODB_IMAGE", "mongo:7")
    container = MongoDbContainer(image)
    container.start()

    url = container.get_connection_url()
    host = container.get_container_host_ip()
    port = int(container.get_exposed_port(27017))
    return container, MongoInfo(url=url, host=host, port=port)


def start_elasticsearch():
    _require_testcontainers()
    from testcontainers.elasticsearch import ElasticsearchContainer

    image = os.getenv("TESTCONTAINERS_ELASTIC_IMAGE", "docker.elastic.co/elasticsearch/elasticsearch:8.11.1")
    container = ElasticsearchContainer(image)
    container.start()

    # testcontainers returns something like http://host:port
    url = container.get_url()
    host = container.get_container_host_ip()
    port = int(container.get_exposed_port(9200))
    wait_for_http_ok(f"{url}/_cluster/health", timeout_s=90.0)
    return container, ElasticsearchInfo(url=url, host=host, port=port)


def start_camunda():
    """
    Starts Camunda Run (7.20) and returns (container, CamundaInfo).
    """
    _require_testcontainers()
    from testcontainers.core.container import DockerContainer

    image = os.getenv("TESTCONTAINERS_CAMUNDA_IMAGE", "camunda/camunda-bpm-platform:run-7.20.0")
    container = DockerContainer(image).with_exposed_ports(8080)
    container.start()

    host = container.get_container_host_ip()
    port = int(container.get_exposed_port(8080))
    engine_rest = f"http://{host}:{port}/engine-rest"
    wait_for_http_ok(f"{engine_rest}/version", timeout_s=90.0)
    return container, CamundaInfo(url=engine_rest, host=host, port=port)

