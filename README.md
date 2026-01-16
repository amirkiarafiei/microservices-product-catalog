# TMF Product Catalog Microservices System

A cloud-native, event-driven microservices platform for managing telecommunications product catalogs. This project demonstrates high-scale architectural patterns including **Distributed Sagas**, **CQRS**, and **Transactional Outbox**.

---

## 🏗 Core Architecture Patterns

- **Hexagonal Architecture:** Domain logic is strictly isolated from infrastructure.
- **Orchestrated Saga:** Publication lifecycle managed by **Camunda BPMN** with automatic compensating transactions.
- **CQRS:** Separate write models (PostgreSQL) and read models (MongoDB + Elasticsearch).
- **Transactional Outbox:** Guaranteed event delivery using Postgres `LISTEN/NOTIFY`.
- **Zero-Trust Security:** Every service boundary validates JWTs signed with **RS256**.
- **Full Observability:** Distributed tracing with **OpenTelemetry** and centralized logging with **ELK**.

---

## 📂 Microservices Map

| Service | Responsibility | Write DB | Read/Search |
| :--- | :--- | :--- | :--- |
| **API Gateway** | Entry point, Circuit Breakers, Correlation IDs | - | - |
| **Identity** | Authentication & RSA Key Distribution | PostgreSQL | - |
| **Characteristic**| Atomic attributes (Speed, Color, etc.) | PostgreSQL | - |
| **Specification** | Technical groupings of characteristics | PostgreSQL | - |
| **Pricing** | Monetary definitions & Saga Locking | PostgreSQL | - |
| **Offering** | Product bundles & Saga Orchestrator | PostgreSQL | - |
| **Store Query** | High-performance catalog & Full-text search | - | Mongo + ES |

---

## 🚀 Quick Start

### 1. Prerequisites
- **Docker & Docker Compose**
- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** package manager

### 2. Infrastructure Setup
Spin up the complete stack (Databases, Broker, Workflow, Tracing, ELK):
```bash
docker compose up -d
```

### 3. Security Setup (RSA Keys)
Generate the keys used for zero-trust JWT signing:
```bash
./scripts/generate_keys.sh
```
*Follow the script instructions to update `services/identity-service/.env`.*

### 4. Database Migrations
Apply schemas to all PostgreSQL write databases:
```bash
python scripts/migrate.py upgrade head
```

### 5. Running the Services
You can run services locally for debugging:
```bash
# Example: Offering Service
cd services/offering-service
uv run uvicorn offering.main:app --reload --port 8005
```

---

## 🕵️ Observability & Monitoring

The system is a "Glass Box" – you can see everything happening inside:

- **Zipkin (Tracing):** Visit [http://localhost:9411](http://localhost:9411) to see waterfall charts of every request hop.
- **Kibana (Logs):** Visit [http://localhost:5601](http://localhost:5601) to search logs by `correlation_id` across all services.
- **Camunda Cockpit:** Visit [http://localhost:8085](http://localhost:8085) to watch the Offering Publication Saga in real-time.

---

## 🧪 Testing

We maintain a high-quality bar with **98+ tests** across the suite:

```bash
# Run tests for a specific service
cd services/pricing-service && uv run pytest tests -v

# Run shared library tests
cd libs/common-python && uv run pytest tests -v
```

---

## 🗺 Implementation Progress

- [x] **Phase 1-10:** Core microservices and CQRS
- [x] **Phase 11:** API Gateway & Resilience
- [x] **Phase 12:** Distributed Transactions (Camunda Saga)
- [x] **Phase 13:** Observability (OTel + ELK)
- [ ] **Phase 14-18:** Frontend (NextJS Implementation) - *Coming Next*
