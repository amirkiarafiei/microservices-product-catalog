import os
import signal
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Generator, List

import psycopg2
import pytest
from common.testing.containers import (
    start_camunda,
    start_elasticsearch,
    start_mongodb,
    start_postgres,
    start_rabbitmq,
    wait_for_http_ok,
)
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from scripts.deploy_camunda_bpmn import deploy_bpmn


def _generate_rsa_keypair() -> tuple[str, str]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


def _create_db(host: str, port: int, user: str, password: str, dbname: str):
    conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname="postgres")
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(f'CREATE DATABASE "{dbname}";')
    except psycopg2.errors.DuplicateDatabase:
        pass
    finally:
        conn.close()


def _run(cmd: list[str], cwd: Path, env: dict):
    subprocess.run(cmd, cwd=str(cwd), env=env, check=True)


def _start_process(name: str, cmd: list[str], cwd: Path, env: dict, log_dir: Path) -> subprocess.Popen:
    log_dir.mkdir(parents=True, exist_ok=True)
    out = (log_dir / f"{name}.log").open("wb")
    return subprocess.Popen(cmd, cwd=str(cwd), env=env, stdout=out, stderr=subprocess.STDOUT)


def _stop_process(p: subprocess.Popen):
    if p.poll() is not None:
        return
    try:
        p.send_signal(signal.SIGTERM)
        p.wait(timeout=10)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass


@dataclass
class E2EContext:
    camunda_url: str
    rabbitmq_url: str
    mongo_url: str
    elastic_url: str
    jwt_private_key: str
    jwt_public_key: str
    services: Dict[str, str]  # name -> base url
    procs: List[subprocess.Popen]
    ports: Dict[str, int]


def _free_port() -> int:
    s = socket.socket()
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return int(port)


@pytest.fixture(scope="session")
def e2e_ctx() -> Generator[E2EContext, None, None]:
    project_root = Path(__file__).resolve().parents[2]
    log_dir = project_root / "logs" / "e2e"

    # --- Infra containers ---
    pg_container, pg = start_postgres(dbname="e2e_bootstrap")
    rmq_container, rmq = start_rabbitmq()
    mongo_container, mongo = start_mongodb()
    es_container, es = start_elasticsearch()
    cam_container, cam = start_camunda()

    private_key, public_key = _generate_rsa_keypair()

    try:
        ports = {
            "gateway": _free_port(),
            "identity": _free_port(),
            "characteristic": _free_port(),
            "specification": _free_port(),
            "pricing": _free_port(),
            "offering": _free_port(),
            "store": _free_port(),
        }
        urls = {k: f"http://localhost:{v}" for k, v in ports.items()}

        # --- DBs ---
        for dbname in ["identity_db", "characteristic_db", "specification_db", "pricing_db", "offering_db"]:
            _create_db(pg.host, pg.port, pg.username, pg.password, dbname)

        # --- Migrations ---
        def db_url(dbname: str) -> str:
            return f"postgresql://{pg.username}:{pg.password}@{pg.host}:{pg.port}/{dbname}"

        migrate_env_base = os.environ.copy()
        migrate_env_base["TRACING_ENABLED"] = "false"

        for svc in ["identity-service", "characteristic-service", "specification-service", "pricing-service", "offering-service"]:
            env = migrate_env_base.copy()
            env["DATABASE_URL"] = db_url(svc.replace("-service", "_db"))
            _run(["python", "scripts/migrate.py", "--service", svc, "upgrade", "head"], cwd=project_root, env=env)

        # --- Service env base ---
        base_env = os.environ.copy()
        base_env["TRACING_ENABLED"] = "false"
        base_env["JWT_PUBLIC_KEY"] = public_key
        base_env["RABBITMQ_URL"] = rmq.amqp_url
        base_env["CAMUNDA_URL"] = cam.url

        # Identity needs keys
        identity_env = base_env.copy()
        identity_env["DATABASE_URL"] = db_url("identity_db")
        identity_env["JWT_PRIVATE_KEY"] = private_key
        identity_env["JWT_PUBLIC_KEY"] = public_key

        # Other services
        char_env = base_env.copy()
        char_env["DATABASE_URL"] = db_url("characteristic_db")

        spec_env = base_env.copy()
        spec_env["DATABASE_URL"] = db_url("specification_db")

        pricing_env = base_env.copy()
        pricing_env["DATABASE_URL"] = db_url("pricing_db")

        offering_env = base_env.copy()
        offering_env["DATABASE_URL"] = db_url("offering_db")
        offering_env["SPECIFICATION_SERVICE_URL"] = urls["specification"]
        offering_env["PRICING_SERVICE_URL"] = urls["pricing"]
        offering_env["CAMUNDA_URL"] = cam.url

        store_env = base_env.copy()
        store_env["MONGODB_URL"] = mongo.url
        store_env["MONGODB_DB_NAME"] = "store_e2e"
        store_env["ELASTICSEARCH_URL"] = es.url
        store_env["ELASTICSEARCH_INDEX"] = "offerings_e2e"
        store_env["CHARACTERISTIC_SERVICE_URL"] = urls["characteristic"]
        store_env["SPECIFICATION_SERVICE_URL"] = urls["specification"]
        store_env["PRICING_SERVICE_URL"] = urls["pricing"]
        store_env["OFFERING_SERVICE_URL"] = urls["offering"]

        gateway_env = base_env.copy()
        gateway_env["IDENTITY_SERVICE_URL"] = urls["identity"]
        gateway_env["CHARACTERISTIC_SERVICE_URL"] = urls["characteristic"]
        gateway_env["SPECIFICATION_SERVICE_URL"] = urls["specification"]
        gateway_env["PRICING_SERVICE_URL"] = urls["pricing"]
        gateway_env["OFFERING_SERVICE_URL"] = urls["offering"]
        gateway_env["STORE_SERVICE_URL"] = urls["store"]

        # --- Start services ---
        procs: List[subprocess.Popen] = []
        procs.append(_start_process("identity", ["uv", "run", "uvicorn", "src.main:app", "--port", str(ports["identity"])], project_root / "services/identity-service", identity_env, log_dir))
        procs.append(_start_process("characteristic", ["uv", "run", "uvicorn", "src.main:app", "--port", str(ports["characteristic"])], project_root / "services/characteristic-service", char_env, log_dir))
        procs.append(_start_process("specification", ["uv", "run", "uvicorn", "src.main:app", "--port", str(ports["specification"])], project_root / "services/specification-service", spec_env, log_dir))
        procs.append(_start_process("pricing", ["uv", "run", "uvicorn", "pricing.main:app", "--port", str(ports["pricing"])], project_root / "services/pricing-service", pricing_env, log_dir))
        procs.append(_start_process("offering", ["uv", "run", "uvicorn", "offering.main:app", "--port", str(ports["offering"])], project_root / "services/offering-service", offering_env, log_dir))
        procs.append(_start_process("store", ["uv", "run", "uvicorn", "store.main:app", "--port", str(ports["store"])], project_root / "services/store-service", store_env, log_dir))
        procs.append(_start_process("gateway", ["uv", "run", "uvicorn", "gateway.main:app", "--port", str(ports["gateway"])], project_root / "services/api-gateway", gateway_env, log_dir))

        # Wait for health
        for name, url in urls.items():
            wait_for_http_ok(f"{url}/health", timeout_s=90.0)

        # --- Deploy BPMN ---
        bpmn_path = project_root / "docs/camunda/offering_publication_saga.bpmn"
        deploy_bpmn(cam.url, str(bpmn_path), deployment_name="offering-publication-saga-e2e")

        ctx = E2EContext(
            camunda_url=cam.url,
            rabbitmq_url=rmq.amqp_url,
            mongo_url=mongo.url,
            elastic_url=es.url,
            jwt_private_key=private_key,
            jwt_public_key=public_key,
            services={
                **urls,
            },
            procs=procs,
            ports=ports,
        )
        yield ctx
    finally:
        # stop services
        for p in reversed(locals().get("procs", [])):
            _stop_process(p)

        cam_container.stop()
        es_container.stop()
        mongo_container.stop()
        rmq_container.stop()
        pg_container.stop()


@pytest.fixture
def start_worker(e2e_ctx):
    """
    Factory to start saga worker processes per test, so tests can control ordering.
    """
    project_root = Path(__file__).resolve().parents[2]
    log_dir = project_root / "logs" / "e2e"

    def _start(kind: str) -> subprocess.Popen:
        env = os.environ.copy()
        env["TRACING_ENABLED"] = "false"
        env["CAMUNDA_URL"] = e2e_ctx.camunda_url
        env["IDENTITY_SERVICE_URL"] = e2e_ctx.services["identity"]
        env["PRICING_API_URL"] = e2e_ctx.services["pricing"]
        env["SPECIFICATION_API_URL"] = e2e_ctx.services["specification"]
        env["OFFERING_API_URL"] = e2e_ctx.services["offering"]
        env["STORE_API_URL"] = e2e_ctx.services["store"]

        if kind == "pricing":
            return _start_process(
                "worker_pricing",
                ["uv", "run", "python", "-c", "from saga_worker import run_pricing_worker; run_pricing_worker()"],
                project_root / "services/pricing-service",
                env,
                log_dir,
            )
        if kind == "spec":
            return _start_process(
                "worker_spec",
                ["uv", "run", "python", "-c", "from saga_worker import run_specification_worker; run_specification_worker()"],
                project_root / "services/specification-service",
                env,
                log_dir,
            )
        if kind == "store":
            return _start_process(
                "worker_store",
                ["uv", "run", "python", "-c", "from store.saga_worker import run_store_worker; run_store_worker()"],
                project_root / "services/store-service",
                env,
                log_dir,
            )
        if kind == "offering":
            return _start_process(
                "worker_offering",
                ["uv", "run", "python", "-c", "from offering.saga_worker import run_offering_worker; run_offering_worker()"],
                project_root / "services/offering-service",
                env,
                log_dir,
            )
        raise ValueError(f"Unknown worker kind: {kind}")

    procs: List[subprocess.Popen] = []

    def factory(kind: str) -> subprocess.Popen:
        p = _start(kind)
        procs.append(p)
        return p

    yield factory

    for p in reversed(procs):
        _stop_process(p)

