# High-Level System Design Document
## TMF Product Catalog Microservices System

**Project:** BLM5126 Term Project  
**Architecture:** Event-Driven Microservices with CQRS & Saga  
**Stack:** Python (FastAPI), NextJS, Docker, Kubernetes

---

### 1. Executive Summary
This project is a cloud-native application designed to demonstrate advanced microservice patterns. It implements a **Telecommunications Product Catalog**, allowing administrators to define technical resources and pricing, bundle them into product offerings, and publish them to a customer-facing store.

The system enforces a strict separation of concerns using **Domain-Driven Design (DDD)**, ensures data consistency via **Distributed Sagas**, and optimizes read performance using **CQRS**.

---

### 2. System Architecture

The system follows a **Hexagonal Architecture** within a **Monorepo**, orchestrated by Docker Compose.

#### 2.1 High-Level Architecture Overview

This diagram shows the main components and their interactions at a conceptual level.

```mermaid
graph TD
    User((User)) --> Client[NextJS Frontend]
    Client --> Gateway[API Gateway]
    
    subgraph "Write Side (PostgreSQL)"
        Gateway --> ID[Identity Service]
        Gateway --> Char[Characteristic Service]
        Gateway --> Spec[Specification Service]
        Gateway --> Price[Pricing Service]
        Gateway --> Offer[Offering Service]
    end
    
    subgraph "Orchestration"
        Offer -- "Start Saga" --> Camunda[Camunda Engine]
        Camunda -- "Task" --> Price
        Camunda -- "Task" --> Spec
        Camunda -- "Task" --> Store
    end

    subgraph "Async Messaging"
        Char -- "Event" --> RabbitMQ
        Spec -- "Event" --> RabbitMQ
        Price -- "Event" --> RabbitMQ
        Offer -- "Event" --> RabbitMQ
    end
    
    subgraph "Read Side (CQRS)"
        RabbitMQ -- "Consume" --> Store[Store Query Service]
        Store --> Mongo[(MongoDB)]
        Store --> Elastic[(Elasticsearch)]
    end
    
    Gateway --> Store
    
    subgraph "Observability"
        Zipkin[Zipkin Tracing]
        ELK[ELK Stack]
    end
```

#### 2.2 Mid-Level Architecture Diagram

This diagram shows bounded contexts, database-per-service pattern, event flows, and key infrastructure with moderate detail.

```mermaid
graph TB
    %% ===== ACTORS & FRONTEND =====
    User((User))
    Admin((Admin))
    Frontend[NextJS Frontend<br/>:3000]
    
    User --> Frontend
    Admin --> Frontend
    Frontend --> Gateway
    
    %% ===== API GATEWAY =====
    Gateway[API Gateway<br/>:8000<br/>JWT Validation + Circuit Breaker]
    
    %% ===== IDENTITY =====
    subgraph IdentityCtx["Identity Context"]
        AuthSvc[Identity Service<br/>:8001]
        AuthDB[(PostgreSQL<br/>users)]
    end
    Gateway -->|/auth/*| AuthSvc --> AuthDB
    
    %% ===== RESOURCE CONTEXT =====
    subgraph ResourceCtx["Resource Context"]
        CharSvc[Characteristic Service<br/>:8002]
        CharDB[(PostgreSQL<br/>characteristics)]
        SpecSvc[Specification Service<br/>:8003]
        SpecDB[(PostgreSQL<br/>specifications)]
    end
    Gateway -->|/characteristics/*| CharSvc --> CharDB
    Gateway -->|/specifications/*| SpecSvc --> SpecDB
    SpecSvc -.->|Subscribes to Events| RabbitMQ
    
    %% ===== COMMERCIAL CONTEXT =====
    subgraph CommercialCtx["Commercial Context"]
        PriceSvc[Pricing Service<br/>:8004]
        PriceDB[(PostgreSQL<br/>pricing)]
    end
    Gateway -->|/prices/*| PriceSvc --> PriceDB
    
    %% ===== PRODUCT CONTEXT =====
    subgraph ProductCtx["Product Context"]
        OfferSvc[Offering Service<br/>:8005<br/>Saga Orchestrator]
        OfferDB[(PostgreSQL<br/>offerings)]
    end
    Gateway -->|/offerings/*| OfferSvc --> OfferDB
    
    %% ===== SAGA ORCHESTRATION =====
    subgraph Orchestration["Saga Orchestration"]
        Camunda[Camunda 7<br/>BPMN Engine]
    end
    OfferSvc -->|Start Saga| Camunda
    Camunda -->|Lock Price| PriceSvc
    Camunda -->|Validate Spec| SpecSvc
    Camunda -->|Index Offering| StoreSvc
    
    %% ===== EVENT BUS =====
    subgraph EventBus["Event Bus"]
        RabbitMQ[RabbitMQ]
        Outbox[Outbox Pattern<br/>LISTEN/NOTIFY]
    end
    CharDB & SpecDB & PriceDB & OfferDB -.->|pg_notify| Outbox
    Outbox -->|Publish| RabbitMQ
    
    %% ===== SALES CONTEXT (CQRS READ) =====
    subgraph SalesCtx["Sales Context (CQRS Read)"]
        StoreSvc[Store Query Service<br/>:8006]
        MongoDB[(MongoDB<br/>Denormalized Views)]
        Elastic[(Elasticsearch<br/>Search Index)]
    end
    Gateway -->|/store/*| StoreSvc
    StoreSvc --> MongoDB
    StoreSvc --> Elastic
    RabbitMQ -->|Events| StoreSvc
    
    %% ===== OBSERVABILITY =====
    subgraph Observability["Observability"]
        Zipkin[Zipkin<br/>Distributed Tracing]
        ELK[ELK Stack<br/>Centralized Logging]
    end
    Gateway & AuthSvc & CharSvc & SpecSvc & PriceSvc & OfferSvc & StoreSvc -->|Traces| Zipkin
    Gateway & AuthSvc & CharSvc & SpecSvc & PriceSvc & OfferSvc & StoreSvc -->|Logs| ELK
    
    %% ===== STYLING =====
    style IdentityCtx fill:#f8d7da,stroke:#721c24
    style ResourceCtx fill:#cce5ff,stroke:#0066cc
    style CommercialCtx fill:#fff2cc,stroke:#cc9900
    style ProductCtx fill:#d4edda,stroke:#28a745
    style SalesCtx fill:#d1ecf1,stroke:#17a2b8
    style Orchestration fill:#f5c6cb,stroke:#dc3545
    style EventBus fill:#e2d5f1,stroke:#6f42c1
    style Observability fill:#ffeeba,stroke:#856404
```

#### 2.3 Detailed Architecture Diagram

This diagram provides a comprehensive view of all components, data flows, patterns, and infrastructure.

```mermaid
graph TB
    %% ===== ACTORS =====
    User((Customer))
    Admin((Admin))
    
    %% ===== FRONTEND LAYER =====
    subgraph FrontendLayer["Frontend Layer (NextJS 14+)"]
        AdminUI[Admin UI<br/>Builder & Viewer Pages]
        StoreUI[Store UI<br/>Public Catalog]
    end
    
    Admin --> AdminUI
    User --> StoreUI
    
    %% ===== API GATEWAY =====
    subgraph GatewayLayer["API Gateway Layer"]
        Gateway[API Gateway<br/>:8000]
        CircuitBreaker[Circuit Breaker<br/>Failure Threshold: 5]
        RateLimiter[Rate Limiter]
        CORSHandler[CORS Handler]
    end
    
    AdminUI --> Gateway
    StoreUI --> Gateway
    Gateway --> CircuitBreaker
    Gateway --> RateLimiter
    Gateway --> CORSHandler
    
    %% ===== IDENTITY SERVICE =====
    subgraph IdentityContext["Identity Context"]
        AuthSvc[Identity Service<br/>:8001]
        AuthDB[(PostgreSQL<br/>users schema)]
        JWTKeys[RS256 Keys<br/>Public/Private]
    end
    
    Gateway -->|/api/v1/auth/*| AuthSvc
    AuthSvc --> AuthDB
    AuthSvc --> JWTKeys
    
    %% ===== RESOURCE CONTEXT =====
    subgraph ResourceContext["Resource Context (Bounded Context)"]
        subgraph CharService["Characteristic Service :8002"]
            CharAPI[REST API]
            CharDomain[Domain Layer<br/>Characteristic Entity]
            CharRepo[Repository]
            CharOutbox[Outbox Publisher]
        end
        CharDB[(PostgreSQL<br/>characteristics schema<br/>+ outbox table)]
        
        subgraph SpecService["Specification Service :8003"]
            SpecAPI[REST API]
            SpecDomain[Domain Layer<br/>Specification Aggregate]
            SpecRepo[Repository]
            SpecOutbox[Outbox Publisher]
            SpecValidator[Cross-Service Validator]
        end
        SpecDB[(PostgreSQL<br/>specifications schema<br/>+ outbox table)]
    end
    
    Gateway -->|/api/v1/characteristics/*| CharAPI
    CharAPI --> CharDomain --> CharRepo --> CharDB
    CharRepo --> CharOutbox
    
    Gateway -->|/api/v1/specifications/*| SpecAPI
    SpecAPI --> SpecDomain --> SpecRepo --> SpecDB
    SpecRepo --> SpecOutbox
    SpecValidator -->|Read Local Cache| SpecDB
    SpecSvcSubscriber[Event Subscriber] -.->|Characteristic Events| SpecDB
    RabbitMQ -.-> SpecSvcSubscriber
    
    %% ===== COMMERCIAL CONTEXT =====
    subgraph CommercialContext["Commercial Context (Bounded Context)"]
        subgraph PriceService["Pricing Service :8004"]
            PriceAPI[REST API]
            PriceDomain[Domain Layer<br/>Price Entity]
            PriceRepo[Repository]
            PriceOutbox[Outbox Publisher]
            PriceLock[Lock Manager<br/>Saga Participation]
        end
        PriceDB[(PostgreSQL<br/>pricing schema<br/>+ outbox table)]
    end
    
    Gateway -->|/api/v1/prices/*| PriceAPI
    PriceAPI --> PriceDomain --> PriceRepo --> PriceDB
    PriceRepo --> PriceOutbox
    PriceDomain --> PriceLock
    
    %% ===== PRODUCT CONTEXT =====
    subgraph ProductContext["Product Context (Bounded Context)"]
        subgraph OfferService["Offering Service :8005"]
            OfferAPI[REST API]
            OfferDomain[Domain Layer<br/>ProductOffering Aggregate Root]
            OfferRepo[Repository]
            OfferOutbox[Outbox Publisher]
            SagaInitiator[Saga Initiator]
            LifecycleSM[Lifecycle State Machine<br/>DRAFT→PUBLISHING→PUBLISHED→RETIRED]
        end
        OfferDB[(PostgreSQL<br/>offerings schema<br/>+ outbox table)]
    end
    
    Gateway -->|/api/v1/offerings/*| OfferAPI
    OfferAPI --> OfferDomain --> OfferRepo --> OfferDB
    OfferRepo --> OfferOutbox
    OfferDomain --> LifecycleSM
    OfferDomain --> SagaInitiator
    
    %% ===== SAGA ORCHESTRATION =====
    subgraph SagaOrchestration["Saga Orchestration Layer"]
        Camunda[Camunda 7<br/>BPMN Engine]
        subgraph SagaSteps["Publication Saga Steps"]
            Step1["-> 1 Lock Prices"]
            Step2["-> 2 Validate Specs"]
            Step3["-> 3 Index in Store"]
            Step4["-> 4 Mark Published"]
            Compensate["Compensating Transactions<br/>Unlock Prices / Rollback"]
        end
    end
    
    SagaInitiator -->|Start Process| Camunda
    Camunda --> Step1 -->|External Task| PriceLock
    Camunda --> Step2 -->|External Task| SpecValidator
    Camunda --> Step3 -->|External Task| StoreIndexer
    Camunda --> Step4 -->|Complete| LifecycleSM
    Step1 & Step2 & Step3 -.->|On Failure| Compensate
    
    %% ===== EVENT MESSAGING =====
    subgraph EventBus["Event Bus (RabbitMQ)"]
        RabbitMQ[RabbitMQ<br/>Message Broker]
        subgraph Topics["Event Topics"]
            CharTopic[resource.characteristics.events]
            SpecTopic[resource.specifications.events]
            PriceTopic[commercial.pricing.events]
            OfferTopic[product.offerings.events]
        end
        DLQ[Dead Letter Queue<br/>Failed Events]
    end
    
    subgraph OutboxPattern["Transactional Outbox Pattern"]
        OutboxInstances[Outbox Listener<br/>PostgreSQL LISTEN/NOTIFY]
    end
    
    CharDB -.->|pg_notify| OutboxInstances
    SpecDB -.->|pg_notify| OutboxInstances
    PriceDB -.->|pg_notify| OutboxInstances 
    OfferDB -.->|pg_notify| OutboxInstances
    OutboxInstances -->|Publish| RabbitMQ
    RabbitMQ --> CharTopic & SpecTopic & PriceTopic & OfferTopic
    RabbitMQ -.-> DLQ
    
    %% ===== SALES CONTEXT (CQRS READ) =====
    subgraph SalesContext["Sales Context - CQRS Read Side"]
        subgraph StoreService["Store Query Service :8006"]
            StoreAPI[REST API<br/>Search & Filter]
            StoreIndexer[Event Consumer<br/>Projection Builder]
            SearchEngine[Search Handler]
            IdempotencyChecker[Idempotency Check<br/>Event ID Tracking]
        end
        MongoDB[(MongoDB 7+<br/>Denormalized Documents<br/>PublishedOffering)]
        Elasticsearch[(Elasticsearch 8+<br/>Full-text Search Index<br/>Faceted Filtering)]
    end
    
    Gateway -->|/api/v1/store/*| StoreAPI
    StoreAPI --> SearchEngine
    SearchEngine --> MongoDB
    SearchEngine --> Elasticsearch
    
    CharTopic -->|CharacteristicCreated/Updated| StoreIndexer
    SpecTopic -->|SpecificationCreated/Updated| StoreIndexer
    PriceTopic -->|PriceUpdated| StoreIndexer
    OfferTopic -->|OfferingPublished/Retired| StoreIndexer
    StoreIndexer --> IdempotencyChecker
    StoreIndexer -->|Upsert| MongoDB
    StoreIndexer -->|Index| Elasticsearch
    
    %% ===== OBSERVABILITY =====
    subgraph Observability["Observability Stack"]
        subgraph Tracing["Distributed Tracing"]
            Zipkin[Zipkin Server]
            TraceCollector[OpenTelemetry Collector]
        end
        subgraph Logging["Centralized Logging"]
            Logstash[Logstash<br/>Log Aggregator]
            LogES[(Elasticsearch<br/>Log Storage)]
            Kibana[Kibana<br/>Log Visualization]
        end
        CorrelationID[Correlation ID<br/>X-Correlation-ID Header]
    end
    
    Gateway -->|Trace Context| TraceCollector --> Zipkin
    AuthSvc -->|Trace Context| TraceCollector
    CharAPI -->|Trace Context| TraceCollector
    SpecAPI -->|Trace Context| TraceCollector
    PriceAPI -->|Trace Context| TraceCollector
    OfferAPI -->|Trace Context| TraceCollector
    StoreAPI -->|Trace Context| TraceCollector
    Camunda -->|Trace Context| TraceCollector
    CharService & SpecService & PriceService & OfferService & StoreService -->|JSON Logs| Logstash
    Logstash --> LogES --> Kibana
    Gateway --> CorrelationID
    
    %% ===== SHARED CHASSIS =====
    subgraph SharedChassis["Shared Chassis Library (libs/common-python)"]
        LogModule[Logging Module<br/>Structured JSON + Correlation ID]
        SecModule[Security Module<br/>JWT Validation + RBAC]
        MsgModule[Messaging Module<br/>Publisher/Consumer Wrappers]
        OutboxModule[Outbox Module<br/>LISTEN/NOTIFY Handler]
        ExcModule[Exception Classes<br/>Standard Error Responses]
    end
    
    CharService & SpecService & PriceService & OfferService & StoreService & AuthSvc -.->|Import| SharedChassis
    
    %% ===== STYLING =====
    style GatewayLayer fill:#ffcccc,stroke:#cc0000
    style ResourceContext fill:#cce5ff,stroke:#0066cc
    style CommercialContext fill:#fff2cc,stroke:#cc9900
    style ProductContext fill:#d4edda,stroke:#28a745
    style SalesContext fill:#d1ecf1,stroke:#17a2b8
    style SagaOrchestration fill:#f5c6cb,stroke:#dc3545
    style EventBus fill:#e2d5f1,stroke:#6f42c1
    style Observability fill:#ffeeba,stroke:#856404
    style SharedChassis fill:#e9ecef,stroke:#495057
    style IdentityContext fill:#f8d7da,stroke:#721c24
```

---

### 3. Microservice Decomposition

The system is composed of 6 autonomous services:

| Service | Type | Responsibility & Pattern | Status |
| :--- | :--- | :--- | :--- |
| **Identity Service** | Utility | **Authentication.** Issues and validates JWTs (RS256). Implements Zero Trust security with locally generated RSA key pairs. | ✅ Implemented |
| **Characteristic Service** | Write | **Resource Context.** Manages atomic attributes (e.g., "Internet Speed", "Color"). Uses Outbox Pattern. | ✅ Implemented (CRUD + Events) |
| **Specification Service** | Write | **Resource Context.** Groups characteristics into technical specs. Validates dependencies synchronously. | ✅ Implemented (CRUD + Sync) |
| **Pricing Service** | Write | **Commercial Context.** Manages monetary definitions. Supports "Locking" during active Sagas. | ✅ Implemented |
| **Offering Service** | Write | **Product Context (Aggregate Root).** Bundles Specs + Prices. **Saga Orchestrator** for publication lifecycle. | ✅ Implemented (Lifecycle + Validation) |
| **Store Query Service** | Read | **Sales Context (CQRS View).** Consumes events to build a read-optimized, searchable catalog (Elasticsearch/Mongo). | ✅ Implemented (CQRS + Search) |

---

### 4. Key Functional Requirements

#### 4.1 Product Builder (Admin)
*   **Define Resources:** Create Characteristics (e.g., "Bandwidth") and Specifications (e.g., "Fiber Optic Spec").
*   **Define Commercials:** Create Price plans (e.g., "$50/month").
*   **Bundle Offering:** Create a "Product Offering" (Draft Mode) linking Specs and Prices.
*   **Publishing Lifecycle:** Admin clicks "Publish". The system must validate integrity across services before making it live.

#### 4.2 Product Viewer (Admin/Customer)
*   **Catalog Browsing:** Users can view published products with sub-second latency.
*   **Advanced Search:** Filter products by dynamic characteristics (e.g., "Show me plans with Speed > 100Mbps").
*   **Detail View:** See full product hierarchy (Offering → Spec → Characteristic) in a single view.

---

### 5. Technical & Non-Functional Requirements

1.  **Data Consistency:**
    *   **Database Migrations:** Managed per-service via **Alembic**. A centralized migration engine in the shared chassis ensures schema consistency, while a root-level migration tool allows system-wide updates.
    *   **Transactional Outbox:** No dual-write issues. Database updates and Event publishing happen atomically using Postgres `LISTEN/NOTIFY`.
    *   **Saga Pattern:** Orchestration via **Camunda**. If an offering fails validation during publishing, all changes (e.g., Price locks) are rolled back.

2.  **Resilience:**
    *   **Circuit Breaker:** The API Gateway stops traffic to failing services to prevent cascading outages.
    *   **Statelessness:** Services can be horizontally scaled (demonstrated via Docker replicas).

3.  **Observability:**
    *   **Distributed Tracing:** Every request carries a `Correlation-ID`. Traces are visualized in **Zipkin**.
    *   **Centralized Logging:** JSON logs aggregated in **ELK Stack**.

---

### 6. Technology Stack

*   **Frontend:** NextJS 14 (App Router), TailwindCSS.
*   **Backend:** Python 3.12, FastAPI, `uv` package manager.
*   **Databases:** PostgreSQL 15 (Write), MongoDB/Elasticsearch (Read).
*   **Messaging:** RabbitMQ (Events), Camunda 7 (Workflow).
*   **Infrastructure:** Docker Compose (Dev), Kubernetes (Arch-ready).

---

### 7. Data Flow Examples

**Scenario A: Creating a Characteristic**
1.  Frontend POSTs to Gateway → Characteristic Service.
2.  Service saves to Postgres & inserts 'Event' to Outbox table (Atomic Transaction).
3.  Background Listener detects Outbox insert → Publishes `CharacteristicCreated` to RabbitMQ.
4.  Store Service consumes event → Updates Read-Database.

**Scenario B: Publishing an Offering (The Saga)**
1.  Frontend POSTs "Publish" to Offering Service.
2.  Offering Service starts **Camunda Process**.
3.  **Step 1:** Pricing Service locks the price (via Worker).
4.  **Step 2:** Spec Service validates dependencies (via Worker).
5.  **Step 3:** Store Service pre-creates the view (via Worker).
6.  **Step 4:** Offering Service sets status to `PUBLISHED`.

---

### 8. Deliverables
1.  **Source Code:** Monorepo containing all 6 services + UI.
2.  **Documentation:** This Design Doc + API Specs.
3.  **Demo Video:** 5-minute walkthrough of the "Publishing Saga" and "Store Search."