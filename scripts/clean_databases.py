#!/usr/bin/env python
"""
Clean and reset all databases to a fresh, empty state.

This script:
1. Connects to PostgreSQL and truncates all tables in all service databases
2. Connects to MongoDB and drops all collections
3. Connects to Elasticsearch and deletes all indexes
4. Clears RabbitMQ queues
"""

import sys

import httpx
import pymongo
from sqlalchemy import create_engine, inspect, text


def clean_postgres(
    host: str = "localhost",
    port: int = 5432,
    user: str = "user",
    password: str = "password",
) -> None:
    """Truncate all tables in all PostgreSQL service databases."""
    print("🗑️  Cleaning PostgreSQL databases...")

    databases = [
        "identity_db",
        "characteristic_db",
        "specification_db",
        "pricing_db",
        "offering_db",
    ]

    for db_name in databases:
        try:
            engine = create_engine(
                f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
            )

            with engine.connect() as conn:
                # Drop custom types (ENUMs) first
                conn.execute(text("DROP TYPE IF EXISTS unitofmeasure CASCADE;"))
                conn.commit()

                inspector = inspect(engine)
                tables = inspector.get_table_names()

                if tables:
                    # Drop tables instead of truncate for clean slate
                    for table in tables:
                        print(f"  Dropping {db_name}.{table}...")
                        conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                    conn.commit()
                    print(f"✅ {db_name} cleaned")
                else:
                    print(f"ℹ️  {db_name} has no tables")

            engine.dispose()
        except Exception as e:
            print(f"❌ Error cleaning {db_name}: {e}")
            sys.exit(1)


def clean_mongodb(host: str = "localhost", port: int = 27017) -> None:
    """Drop all MongoDB databases and collections."""
    print("\n🗑️  Cleaning MongoDB...")

    try:
        client = pymongo.MongoClient(f"mongodb://{host}:{port}/", serverSelectionTimeoutMS=5000)

        # List all databases except system databases
        db_names = client.list_database_names()
        db_names = [
            name
            for name in db_names
            if name not in ["admin", "config", "local", "test"]
        ]

        for db_name in db_names:
            print(f"  Dropping database {db_name}...")
            client.drop_database(db_name)
            print(f"✅ {db_name} dropped")

        if not db_names:
            print("ℹ️  No custom databases to clean")

        client.close()
    except Exception as e:
        print(f"❌ Error cleaning MongoDB: {e}")
        sys.exit(1)


def clean_elasticsearch(host: str = "localhost", port: int = 9200) -> None:
    """Delete all indexes from Elasticsearch."""
    print("\n🗑️  Cleaning Elasticsearch...")

    try:
        client = httpx.Client(base_url=f"http://{host}:{port}")

        # Get all indexes
        resp = client.get("/_cat/indices?format=json")
        if resp.status_code != 200:
            print(f"❌ Failed to list Elasticsearch indexes: {resp.status_code}")
            sys.exit(1)

        indexes = resp.json()
        for index in indexes:
            index_name = index["index"]
            # Skip system indexes
            if not index_name.startswith("."):
                print(f"  Deleting index {index_name}...")
                delete_resp = client.delete(f"/{index_name}")
                if delete_resp.status_code in [200, 404]:
                    print(f"✅ {index_name} deleted")
                else:
                    print(f"⚠️  Failed to delete {index_name}: {delete_resp.status_code}")

        if not any(idx["index"] for idx in indexes if not idx["index"].startswith(".")):
            print("ℹ️  No custom indexes found")

        client.close()
    except Exception as e:
        print(f"❌ Error cleaning Elasticsearch: {e}")
        sys.exit(1)


def clean_rabbitmq(
    host: str = "localhost",
    port: int = 15672,
    user: str = "guest",
    password: str = "guest",
) -> None:
    """Purge all RabbitMQ queues."""
    print("\n🗑️  Cleaning RabbitMQ...")

    try:
        client = httpx.Client(base_url=f"http://{host}:{port}")
        client.auth = (user, password)

        # Get all queues
        resp = client.get("/api/queues")
        if resp.status_code != 200:
            print(f"⚠️  Could not connect to RabbitMQ management API: {resp.status_code}")
            print("   (This is OK if RabbitMQ management plugin is not enabled)")
            client.close()
            return

        queues = resp.json()
        for queue in queues:
            queue_name = queue["name"]
            vhost = queue["vhost"]
            # Skip amq.* system queues
            if not queue_name.startswith("amq."):
                print(f"  Purging queue {vhost}/{queue_name}...")
                purge_resp = client.delete(f"/api/queues/{vhost}/{queue_name}/contents")
                if purge_resp.status_code == 204:
                    print(f"✅ {queue_name} purged")
                else:
                    print(
                        f"⚠️  Could not purge {queue_name}: {purge_resp.status_code}"
                    )

        if not any(q["name"] for q in queues if not q["name"].startswith("amq.")):
            print("ℹ️  No custom queues found")

        client.close()
    except Exception as e:
        print(f"⚠️  Error cleaning RabbitMQ: {e}")
        print("   (Continuing anyway - queues can be recreated)")


def main() -> None:
    """Run all cleanup operations."""
    print("=" * 60)
    print("DATABASE CLEANUP SCRIPT")
    print("=" * 60)

    # PostgreSQL
    clean_postgres()

    # MongoDB
    clean_mongodb()

    # Elasticsearch
    clean_elasticsearch()

    # RabbitMQ
    clean_rabbitmq()

    print("\n" + "=" * 60)
    print("✅ All databases cleaned successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run migrations: make migrate")
    print("2. Seed sample data: python scripts/seed_data.py")


if __name__ == "__main__":
    main()
