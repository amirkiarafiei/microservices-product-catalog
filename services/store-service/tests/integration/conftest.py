import os
import sys

import pytest
from common.testing.containers import start_elasticsearch, start_mongodb
from fastapi.testclient import TestClient

# Add src to path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, BASE_DIR)


@pytest.fixture(scope="session")
def infra():
    mongo_container, mongo = start_mongodb()
    es_container, es = start_elasticsearch()
    try:
        yield {"mongo_container": mongo_container, "mongo": mongo, "es_container": es_container, "es": es}
    finally:
        es_container.stop()
        mongo_container.stop()


@pytest.fixture(scope="session", autouse=True)
def configure_clients(infra):
    # Update settings first
    import store.config as config_module  # noqa: E402

    config_module.settings.MONGODB_URL = infra["mongo"].url
    config_module.settings.ELASTICSEARCH_URL = infra["es"].url
    config_module.settings.MONGODB_DB_NAME = "store_test_db"
    config_module.settings.ELASTICSEARCH_INDEX = "offerings_test"

    # Re-create global clients to use new settings
    import store.infrastructure.elasticsearch as es_mod  # noqa: E402
    import store.infrastructure.mongodb as mongo_mod  # noqa: E402
    from store.infrastructure.elasticsearch import ElasticsearchClient  # noqa: E402
    from store.infrastructure.mongodb import MongoDBClient  # noqa: E402

    es_mod.es_client = ElasticsearchClient()
    mongo_mod.mongodb_client = MongoDBClient()

    # Update store.main module-level references (it imported the old instances)
    import store.main as main_mod  # noqa: E402

    main_mod.es_client = es_mod.es_client
    main_mod.mongodb_client = mongo_mod.mongodb_client

    yield

    # Close clients
    try:
        import asyncio
        import store.infrastructure.elasticsearch as es_mod2  # noqa: E402
        import store.infrastructure.mongodb as mongo_mod2  # noqa: E402

        asyncio.run(es_mod2.es_client.close())
        asyncio.run(mongo_mod2.mongodb_client.close())
    except Exception:
        # best-effort cleanup; containers will be stopped anyway
        pass


@pytest.fixture
def client(infra):
    from store.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def mongodb_client():
    import store.infrastructure.mongodb as mongo_mod

    return mongo_mod.mongodb_client


@pytest.fixture
def es_client():
    import store.infrastructure.elasticsearch as es_mod

    return es_mod.es_client

