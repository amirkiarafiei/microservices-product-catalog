# Database Cleanup and Seeding Guide

## Overview

This guide covers how to reset your application to a fresh state and populate it with sample data for testing and development.

## Quick Start

### 1. Clean All Databases

Reset all databases to an empty state:

```bash
make clean-db
```

This script will:
- **PostgreSQL:** Truncate all tables in all service databases (identity_db, characteristic_db, specification_db, pricing_db, offering_db)
- **MongoDB:** Drop all non-system databases
- **Elasticsearch:** Delete all custom indexes
- **RabbitMQ:** Purge all custom queues

### 2. Run Database Migrations

Apply migrations to recreate the schema:

```bash
make migrate
```

### 3. Seed Sample Data

Populate the database with sample entities via API:

```bash
make seed-data
```

This will create:
- 5 sample **characteristics** (Speed, Storage, Reliability, Latency, Bandwidth)
- 3 sample **specifications** (Basic, Premium, Enterprise)
- 4 sample **prices** ($29.99 to $199.99/month)
- 3 sample **offerings** that are automatically published
- All related Elasticsearch indexes for search

## Full Reset Workflow

To completely reset and reinitialize the application:

```bash
# 1. Stop backend services
make stop

# 2. Clean all data
make clean-db

# 3. Run migrations
make migrate

# 4. Seed default users (for identity-service if needed)
cd services/identity-service && DATABASE_URL="postgresql://user:password@localhost:5432/identity_db" uv run python -c "from src.seed import seed_users; seed_users()" && cd ../..

# 5. Start backend services
make backend

# 6. Wait for services to be ready (check logs)
sleep 10

# 7. Seed sample data
make seed-data

# 8. Start frontend (optional)
make frontend
```

Or use this combined one-liner for a complete reset:

```bash
make stop && make clean-db && make migrate && cd services/identity-service && DATABASE_URL="postgresql://user:password@localhost:5432/identity_db" uv run python -c "from src.seed import seed_users; seed_users()" && cd ../.. && make backend && sleep 10 && make seed-data
```

## Individual Scripts

### `scripts/clean_databases.py`

Cleans all databases without requiring API access. Useful when services are down or experiencing issues.

**Usage:**
```bash
python scripts/clean_databases.py
```

**Options (environment variables):**
- `DB_HOST` - PostgreSQL host (default: localhost)
- `DB_PORT` - PostgreSQL port (default: 5432)
- `DB_USER` - PostgreSQL user (default: postgres)
- `DB_PASSWORD` - PostgreSQL password (default: postgres)
- `MONGO_HOST` - MongoDB host (default: localhost)
- `MONGO_PORT` - MongoDB port (default: 27017)
- `ES_HOST` - Elasticsearch host (default: localhost)
- `ES_PORT` - Elasticsearch port (default: 9200)
- `RABBITMQ_HOST` - RabbitMQ management host (default: localhost)
- `RABBITMQ_PORT` - RabbitMQ management port (default: 15672)

**Example with custom host:**
```bash
DB_HOST=prod-db.example.com python scripts/clean_databases.py
```

### `scripts/seed_data.py`

Initializes the application with sample data through API calls. Requires backend services to be running.

**Usage:**
```bash
python scripts/seed_data.py
```

**Options:**
- `--base-url` - API base URL (default: http://localhost:8000)
- `--admin-user` - Admin username (default: admin)
- `--admin-pass` - Admin password (default: admin)

**Example with custom credentials:**
```bash
python scripts/seed_data.py --base-url http://api.example.com --admin-user admin --admin-pass mypassword
```

## What Gets Created

### Characteristics

- Speed (100 Mbps)
- Storage (500 GB)
- Reliability (99.9%)
- Latency (10 ms)
- Bandwidth (1000 Mbps)

### Specifications

1. **Basic Internet Plan** - Speed
2. **Premium Internet Plan** - Speed + Storage
3. **Enterprise Plan** - Speed + Storage + Reliability

### Prices

- $29.99/month
- $49.99/month
- $99.99/month
- $199.99/month

### Offerings (Published)

1. **Basic Fiber Internet** - Basic spec + $29.99 (WEB, PHONE channels)
2. **Premium Fiber Internet** - Premium spec + $49.99 (WEB, PHONE, PARTNER channels)
3. **Enterprise Connectivity** - Enterprise spec + $199.99 (WEB, SALES_TEAM channels)

All offerings are automatically published to the store.

## Verification

After seeding, verify the data:

### 1. Check via API

```bash
# List characteristics
curl -H "Authorization: Bearer $(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"admin\",\"password\":\"admin\"}' | jq -r '.access_token')" \
  http://localhost:8000/api/v1/characteristics

# Search store
curl http://localhost:8000/api/v1/store/search?q=internet
```

### 2. Check Web UI

1. Navigate to http://localhost:3000
2. Login with `admin` / `admin`
3. Go to **Viewer** tab to see all created entities
4. Go to **Store** page to see published offerings

### 3. Check Databases

```bash
# PostgreSQL
docker exec postgres-container psql -U postgres -d offering_db -c "SELECT * FROM offerings;"

# MongoDB
docker exec mongo-container mongosh --eval "db.published_offerings.find().pretty()"

# Elasticsearch
curl http://localhost:9200/offerings/_search?pretty
```

## Troubleshooting

### Clean fails with "Connection refused"

**Issue:** Cannot connect to databases
**Solution:** Make sure Docker containers are running:
```bash
docker ps
make infra-up
```

### Seed fails with "401 Unauthorized"

**Issue:** Cannot login to API
**Solution:**
1. Check identity service is running: `lsof -i :8001`
2. Check JWT keys exist: `ls -la keys/`
3. Verify admin user exists: `cd services/identity-service && DATABASE_URL="postgresql://user:password@localhost:5432/identity_db" uv run python -c "from src.seed import seed_users; seed_users()"`
4. Restart identity service and try again

### Seed fails with "No specifications created"

**Issue:** Characteristics were created but specifications fail
**Solution:**
1. Check that characteristic IDs are valid
2. Ensure specification service is running: `lsof -i :8003`
3. Check service logs: `tail logs/specification.log`

### Some offerings don't publish

**Issue:** Offerings stuck in PUBLISHING state
**Solution:**
1. Check all saga workers are running: `ps aux | grep saga_worker`
2. Check Camunda is available: `curl http://localhost:8085/engine-rest/engine`
3. Review logs: `tail logs/offering.log`

## Customizing Sample Data

To create different sample data, edit `scripts/seed_data.py` and modify the data arrays in these methods:
- `create_characteristics()` - Lines ~100-120
- `create_specifications()` - Lines ~140-160
- `create_prices()` - Lines ~180-200
- `create_offerings()` - Lines ~220-250

Then run:
```bash
make clean-db && make migrate && make backend && sleep 10 && make seed-data
```

## Notes

- **Idempotency:** Seeding can be run multiple times - it will create new entities each time
- **Data Loss:** `make clean-db` is destructive and cannot be undone. Use only in development environments.
- **Performance:** Seeding typically takes 5-10 seconds depending on system performance
- **Elasticsearch:** Store service automatically syncs published offerings to Elasticsearch for search
