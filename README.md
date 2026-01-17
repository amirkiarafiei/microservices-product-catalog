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

## 📊 System Visualizations

### 1. High-Level Architecture
The system is divided into a **Command Side** (Write) and a **Query Side** (Read), connected via asynchronous events.

```mermaid
flowchart TB
    subgraph ClientLayer [Frontend]
        UI[NextJS App]
    end

    subgraph EntryLayer [API Gateway]
        GW[API Gateway]
    end

    subgraph WriteSide [Command Side - PostgreSQL]
        ID[Identity]
        CH[Characteristic]
        SP[Specification]
        PR[Pricing]
        OF[Offering]
    end

    subgraph Orchestration [Orchestration]
        CAM[Camunda Engine]
    end

    subgraph Messaging [Event Bus]
        RMQ[RabbitMQ]
    end

    subgraph ReadSide [Query Side - NoSQL]
        ST[Store Query Service]
        MDB[(MongoDB)]
        ES[(Elasticsearch)]
    end

    UI --> GW
    GW --> WriteSide
    OF -->|"Start Saga"| CAM
    CAM -->|"Tasks"| WriteSide
    WriteSide -->|"Outbox Events"| RMQ
    RMQ --> ST
    ST --> MDB
    ST --> ES
    GW --> ST
```

### 2. Offering Publication Saga
A distributed transaction spanning four microservices, orchestrated by Camunda.

```mermaid
sequenceDiagram
    participant Admin
    participant OF as Offering Service
    participant CAM as Camunda Engine
    participant PR as Pricing Service
    participant SP as Spec Service
    participant ST as Store Service

    Admin->>OF: POST /publish
    OF->>CAM: Start Process
    CAM->>PR: Task: Lock Prices
    PR-->>CAM: Done
    CAM->>SP: Task: Validate Specs
    SP-->>CAM: Done
    CAM->>ST: Task: Pre-create View
    ST-->>CAM: Done
    CAM->>OF: Task: Mark Published
    OF-->>Admin: 200 OK (via Outbox/Event)
```

### 3. Transactional Outbox Pattern
Ensures that a database update and its corresponding event publication happen atomically.

```mermaid
flowchart LR
    subgraph Service [Microservice]
        Logic[Business Logic]
        Repo[Repository]
    end

    subgraph DB [PostgreSQL]
        Data[(Business Data)]
        Outbox[(Outbox Table)]
    end

    subgraph Broker [RabbitMQ]
        Queue[Event Exchange]
    end

    Logic --> Repo
    Repo -->|"Atomic Transaction"| Data
    Repo -->|"Atomic Transaction"| Outbox
    Outbox -->|"pg_notify"| Listener[Outbox Listener]
    Listener -->|"Publish"| Queue
```

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
| **Web UI** | Modern Management & Shopping Portal | - | Next.js 16 |

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
- [x] **Phase 14:** UI Scaffold & Authentication (Next.js 16, Tailwind 4)
- [x] **Phase 15:** Admin UI - The Builder (Create Entities)
- [x] **Phase 16:** Admin UI - The Viewer (Manage Entities)
- [x] **Phase 17:** Customer UI - The Store & Saga Polling
- [ ] **Phase 18:** Final Polish & Deployment
