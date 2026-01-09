# TMF Product Catalog Microservices System

A cloud-native, event-driven microservices platform for managing telecommunications product catalogs.

## 🚀 Quick Start

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.12+
- `uv` package manager

### 2. Infrastructure Setup
Start the shared infrastructure (PostgreSQL, RabbitMQ, MongoDB, etc.):
```bash
docker compose up -d
```

### 3. Security Setup (RSA Keys)
This project uses **RS256** JWT signing. You must generate your own RSA keys locally before running the services.

Run the generation script:
```bash
./scripts/generate_keys.sh
```
The script will generate `private_key.pem` and `public_key.pem` in the `identity-service` folder and provide you with the formatted strings to copy into your `services/identity-service/.env` file.

### 4. Running the Identity Service
```bash
cd services/identity-service
uv run uvicorn src.main:app --reload --port 8001
```

## 🏗 Architecture
- **Hexagonal Architecture**
- **Saga Pattern** (via Camunda)
- **CQRS** (Read side via MongoDB/Elasticsearch)
- **Transactional Outbox** (Postgres LISTEN/NOTIFY)

## 📂 Project Structure
- `services/`: Individual microservices.
- `libs/`: Shared Python chassis (logging, security, etc.).
- `infra/`: Infrastructure configuration files.
- `scripts/`: Utility scripts.
- `docs/`: Technical documentation and requirements.
