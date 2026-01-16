# Software Requirements Specification (SRS)
## TMF Product Catalog Microservices System

**Version:** 1.0  
**Date:** January 2026  
**Course:** BLM5126 - Advanced Software Architecture  
**Author:** [Your Name]

---

# PART I: BACKEND SYSTEM REQUIREMENTS

## 1. INTRODUCTION

### 1.1 Purpose
This document specifies the complete requirements for a microservices-based product catalog management system following TMForum standards. The system demonstrates advanced architectural patterns including CQRS, Event-Driven Architecture, Saga Orchestration, and Domain-Driven Design principles.

### 1.2 Scope
The backend system consists of six microservices orchestrated through an API Gateway, communicating via synchronous REST APIs and asynchronous message brokers. The system manages product characteristics, specifications, pricing, and offerings with full lifecycle management from draft to publication to retirement.

### 1.3 Architectural Goals
- Demonstrate decomposition by business capability (Syllabus 2.2)
- Implement CQRS pattern for read/write separation (Syllabus 7.2)
- Apply Saga orchestration for distributed transactions (Syllabus 4.2)
- Enforce Domain-Driven Design with rich aggregates (Syllabus 5.2)
- Ensure data consistency through Transactional Outbox (Syllabus 5.3)
- Provide full observability and tracing (Syllabus 11.3)

---

## 2. OVERALL SYSTEM ARCHITECTURE

### 2.1 Architectural Style
**Microservices Architecture** with the following characteristics:
- Database-per-service pattern (no shared databases)
- Asynchronous event-driven communication between services
- Synchronous REST for client-gateway and gateway-service communication
- API Gateway as single entry point
- Service mesh capabilities for resilience

### 2.2 Technology Stack Decisions

**Core Technologies:**
- Programming Language: Python 3.12+
- Web Framework: FastAPI (async support, auto-documentation)
- Package Management: uv (workspace management for monorepo)
- Containerization: Docker
- Orchestration: Docker Compose (development), Kubernetes-ready

**Infrastructure Components:**
- Message Broker: RabbitMQ (reliable delivery, dead-letter queues)
- Write Databases: PostgreSQL 15+ (ACID compliance, LISTEN/NOTIFY support)
- Read Database: MongoDB 7+ (document store for denormalized views)
- Search Engine: Elasticsearch 8+ (full-text search, aggregations)
- Workflow Engine: Camunda Platform (BPMN orchestration)
- Distributed Tracing: Zipkin (OpenTelemetry integration)
- Log Aggregation: ELK Stack (Elasticsearch, Logstash, Kibana)
- Identity Provider: Keycloak or custom JWT service

**Quality Attributes:**
- Availability: Circuit breakers prevent cascading failures
- Scalability: Horizontal scaling per service
- Observability: Distributed tracing with correlation IDs
- Security: Zero-trust JWT validation at every service boundary
- Maintainability: Clean Architecture separation of concerns

---

## 3. SERVICE DECOMPOSITION

### 3.1 Bounded Contexts

**Context Map:**

```
┌─────────────────────────────────────────────────────────┐
│                    RESOURCE CONTEXT                      │
│  (Product Attributes & Technical Specifications)        │
│  - Characteristic Service                               │
│  - Specification Service                                │
└─────────────────────────────────────────────────────────┘
                          │
                          │ References by ID
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   COMMERCIAL CONTEXT                     │
│  (Pricing, Currency, Tax Rules)                         │
│  - Pricing Service                                      │
└─────────────────────────────────────────────────────────┘
                          │
                          │ References by ID
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    PRODUCT CONTEXT                       │
│  (Product Offering Lifecycle & Orchestration)           │
│  - Offering Service                                     │
└─────────────────────────────────────────────────────────┘
                          │
                          │ Publishes Events
                          ↓
┌─────────────────────────────────────────────────────────┐
│                     SALES CONTEXT                        │
│  (Customer-Facing Catalog & Search)                     │
│  - Store Query Service (CQRS Read Model)                │
└─────────────────────────────────────────────────────────┘

                CROSS-CUTTING CONTEXT
┌─────────────────────────────────────────────────────────┐
│                   IDENTITY CONTEXT                       │
│  (Authentication & Authorization)                       │
│  - Identity Service                                     │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Service Catalog

#### 3.2.1 Characteristic Service (Write Service)

**Bounded Context:** Resource Context  
**Database:** PostgreSQL (characteristics schema)  
**Responsibility:** Manage atomic product attributes

**Domain Model:**
- **Characteristic (Entity)**
  - Attributes: id (UUID), name (string), value (string), unitOfMeasure (enum), createdAt, updatedAt
  - Business Rules:
    - Name must be unique within the catalog
    - UnitOfMeasure must be from predefined enum: [Mbps, Gbps, MB, GB, TB, GHz, Volt, Watt, Meter, Percent, Seconds, Minutes, Hours, Days, Months, Years, Unit, None]
    - Value must be compatible with unit type (numeric for measurable units)
  - Invariants:
    - Cannot be deleted if referenced by any Specification
    - Updates propagate to all dependent Specifications via events

**Aggregate Root:** Characteristic (self-contained entity)

**Domain Events Published:**
- CharacteristicCreated: When a new characteristic is successfully persisted
- CharacteristicUpdated: When characteristic value or unit changes
- CharacteristicDeleted: When characteristic is removed (only if no dependencies)

**API Endpoints:**
- POST /api/v1/characteristics - Create new characteristic
- GET /api/v1/characteristics/{id} - Retrieve by ID
- GET /api/v1/characteristics - List all (pagination support)
- PUT /api/v1/characteristics/{id} - Update existing
- DELETE /api/v1/characteristics/{id} - Delete (with dependency check)

**Validation Rules:**
- Name: Required, 1-200 characters, alphanumeric with spaces
- Value: Required, 1-100 characters
- UnitOfMeasure: Required, must match enum values
- Deletion: Reject if Specification references exist (query via Repository)

**Error Scenarios:**
- Duplicate name → 409 Conflict
- Invalid unit of measure → 400 Bad Request
- Referenced by specifications → 409 Conflict (cannot delete)
- Not found → 404 Not Found

**Integration Points:**
- Outbox table for transactional event publishing
- RabbitMQ topic: `resource.characteristics.events`
- No synchronous calls to other services

---

#### 3.2.2 Specification Service (Write Service)

**Bounded Context:** Resource Context  
**Database:** PostgreSQL (specifications schema)  
**Responsibility:** Manage technical specifications as collections of characteristics

**Domain Model:**
- **Specification (Aggregate Root)**
  - Attributes: id (UUID), name (string), characteristicIds (List[UUID]), createdAt, updatedAt
  - Business Rules:
    - Must reference at least one valid Characteristic
    - Name must be unique
    - Characteristic IDs must exist in Characteristic Service
  - Invariants:
    - Cannot be created with empty characteristic list
    - Cannot be deleted if referenced by any Product Offering
    - Must validate characteristic existence before creation

**Domain Events Published:**
- SpecificationCreated
- SpecificationUpdated (includes full list of current characteristic IDs)
- SpecificationDeleted

**API Endpoints:**
- POST /api/v1/specifications - Create (requires characteristicIds array)
- GET /api/v1/specifications/{id} - Retrieve with expanded characteristics
- GET /api/v1/specifications - List all
- PUT /api/v1/specifications/{id} - Update (full replacement)
- DELETE /api/v1/specifications/{id} - Delete (with dependency check)

**Validation Rules:**
- Name: Required, unique, 1-200 characters
- CharacteristicIds: Required array, minimum 1 element
- Before creation: Verify all characteristic IDs exist via HTTP call to Characteristic Service
- Deletion: Check Product Offering Service for references

**Cross-Service Validation:**
- **Local Reference Cache:** To ensure autonomy, the Specification Service maintains a local read-only table of valid Characteristic IDs.
- **Event-Driven Synchronization:** The Specification Service subscribes to `resource.characteristics.events` (Created/Deleted) to keep its local cache up to date.
- **Validation:** When creating/updating a Specification, the service validates characteristic existence against its local cache instead of making synchronous HTTP calls.
- **Fallback:** If a referenced characteristic is not yet in the local cache due to eventual consistency lag, the service may return a `400 Bad Request` suggesting a retry or perform a one-time "lazy-load" fetch from the Characteristic Service.

**Event Handling:**
- **Subscribe to:** CharacteristicUpdated events
  - Action: Update local cached data or trigger recalculation if needed
- **Subscribe to:** CharacteristicDeleted events
  - Action: If a Specification references the deleted characteristic, mark as invalid or remove reference (business decision: fail-safe vs fail-fast)

**Error Scenarios:**
- Invalid characteristic ID → 400 Bad Request (include which IDs are invalid)
- Characteristic Service unavailable → 503 Service Unavailable
- Referenced by offerings → 409 Conflict
- Duplicate name → 409 Conflict

**Integration Points:**
- Outbox table for transactional event publishing
- RabbitMQ topic (Subscribe): `resource.characteristics.events`
- RabbitMQ topic (Publish): `resource.specifications.events`
- No synchronous calls to other services

---

#### 3.2.3 Pricing Service (Write Service)

**Bounded Context:** Commercial Context  
**Database:** PostgreSQL (pricing schema)  
**Responsibility:** Manage pricing entities with currency and units

**Domain Model:**
- **Price (Entity)**
  - Attributes: id (UUID), name (string), value (Decimal), unit (string), currency (enum), createdAt, updatedAt
  - Business Rules:
    - Name must be unique
    - Value must be positive decimal (two decimal places)
    - Currency must be ISO 4217 code (USD, EUR, TRY)
    - Unit describes billing period (e.g., "per month", "one-time")
  - Invariants:
    - Cannot be deleted if locked by active Product Offering publication saga
    - Cannot be modified during publication process (locking mechanism)

**Aggregate Root:** Price (self-contained entity)

**Domain Events Published:**
- PriceCreated
- PriceUpdated
- PriceDeleted
- PriceLocked (Saga-related)
- PriceUnlocked (Saga-related)

**API Endpoints:**
- POST /api/v1/prices - Create
- GET /api/v1/prices/{id} - Retrieve
- GET /api/v1/prices - List all
- PUT /api/v1/prices/{id} - Update
- DELETE /api/v1/prices/{id} - Delete
- POST /api/v1/prices/{id}/lock - Lock price (Saga step)
- POST /api/v1/prices/{id}/unlock - Unlock price (Compensating transaction)

**Validation Rules:**
- Name: Required, unique, 1-200 characters
- Value: Required, positive, max 2 decimal places
- Unit: Required, free text, 1-50 characters
- Currency: Required, enum [USD, EUR, TRY]

**Saga Participation:**
- **Locking Mechanism:** Maintain a `locked` boolean flag and `locked_by_saga_id` field
- When Offering publication saga starts, it sends lock command
- Locked prices cannot be deleted or significantly modified
- If saga fails, compensating transaction unlocks price

**Error Scenarios:**
- Duplicate name → 409 Conflict
- Invalid currency → 400 Bad Request
- Price locked → 423 Locked (cannot modify)
- Referenced by offerings → 409 Conflict

**Integration Points:**
- Outbox table for transactional event publishing
- RabbitMQ topic: `commercial.pricing.events`
- Supports Saga locking via `/lock` and `/unlock` endpoints for Offering Service orchestration

---

#### 3.2.4 Product Offering Service (Write Service)

**Bounded Context:** Product Context  
**Database:** PostgreSQL (offerings schema)  
**Responsibility:** Aggregate root managing complete product offerings with lifecycle orchestration

**Domain Model:**
- **ProductOffering (Aggregate Root)**
  - Attributes:
    - id (UUID)
    - name (string)
    - description (string, optional)
    - specificationIds (List[UUID])
    - pricingIds (List[UUID])
    - salesChannels (List[string], e.g., ["online", "retail"])
    - lifecycleStatus (enum: DRAFT, PUBLISHING, PUBLISHED, RETIRED)
    - publishedAt (timestamp, nullable)
    - retiredAt (timestamp, nullable)
    - version (integer, for optimistic locking)
    - createdAt, updatedAt
  
  - Business Rules:
    - Can be created in DRAFT with only name (partial entity)
    - Must have at least one specification, one price, and one sales channel to transition to PUBLISHING
    - Once PUBLISHED, cannot be edited (immutable for audit)
    - Can transition from PUBLISHED to RETIRED
    - RETIRED offerings remain in database but are hidden from Store
    - Cannot delete PUBLISHED or RETIRED offerings (soft delete only)
  
  - Domain Methods:
    - `publish()`: Validates completeness, initiates Camunda saga, transitions to PUBLISHING
    - `confirmPublication()`: Called by saga completion, transitions to PUBLISHED
    - `retire()`: Transitions PUBLISHED → RETIRED
    - `canPublish()`: Validation check (returns boolean + error messages)

**Lifecycle State Machine:**
```
DRAFT → PUBLISHING → PUBLISHED → RETIRED
  ↑         ↓
  └─── (saga fails)
```

**Domain Events Published:**
- OfferingCreated (lifecycle: DRAFT)
- OfferingUpdated (only in DRAFT state)
- OfferingPublicationInitiated (saga started)
- OfferingPublished (saga completed, lifecycle: PUBLISHED)
- OfferingPublicationFailed (saga failed, back to DRAFT)
- OfferingRetired

**API Endpoints:**
- POST /api/v1/offerings - Create draft
- GET /api/v1/offerings/{id} - Retrieve
- GET /api/v1/offerings - List with lifecycle filter
- PUT /api/v1/offerings/{id} - Update (only DRAFT)
- POST /api/v1/offerings/{id}/publish - Initiate publication saga
- POST /api/v1/offerings/{id}/retire - Retire published offering
- DELETE /api/v1/offerings/{id} - Delete (only DRAFT)

**Validation Rules:**
- Name: Required, 1-200 characters
- SpecificationIds: Required for publication, must exist in Specification Service
- PricingIds: Required for publication, must exist in Pricing Service
- SalesChannels: Required for publication, non-empty array
- Lifecycle transitions: Enforce state machine rules

**Saga Orchestration (Publication Process):**

When `POST /offerings/{id}/publish` is called:

1. **Pre-flight Validation:**
   - Check offering is in DRAFT
   - Verify at least one spec, one price, one channel
   - Validate specification IDs exist (HTTP call to Specification Service)
   - Validate pricing IDs exist (HTTP call to Pricing Service)

2. **Saga Initiation:**
   - Create Camunda process instance
   - Pass offering data as process variables
   - Transition offering to PUBLISHING state
   - Publish OfferingPublicationInitiated event

3. **Camunda BPMN Process (Orchestration):**
   
   **Process Name:** `offering-publication-saga`
   
   **Tasks:**
   - **Task 1: Lock Prices**
     - Service: Pricing Service
     - Worker: Polls Camunda for task type `lock-prices`
     - Action: Call POST /prices/{id}/lock for each price ID
     - Success: Complete task with success
     - Failure: Fail task, trigger compensation
   
   - **Task 2: Validate Specifications**
     - Service: Specification Service
     - Worker: Polls for task type `validate-specifications`
     - Action: Verify all specs still exist and are valid
     - Success: Complete task
     - Failure: Fail task, trigger compensation
   
   - **Task 3: Create Store Entry**
     - Service: Store Query Service
     - Worker: Polls for task type `create-store-entry`
     - Action: Pre-create denormalized document in MongoDB
     - Success: Complete task
     - Failure: Fail task, trigger compensation
   
   - **Task 4: Confirm Publication**
     - Service: Offering Service
     - Worker: Polls for task type `confirm-publication`
     - Action: Update offering lifecycle to PUBLISHED, set publishedAt timestamp
     - Success: Complete task, end process
   
   **Compensating Transactions (if any task fails):**
   - Unlock all locked prices (Pricing Service)
   - Delete partial store entry (Store Service)
   - Revert offering to DRAFT (Offering Service)
   - Publish OfferingPublicationFailed event

**Camunda Worker Implementation Pattern:**
Each service must implement an External Task Worker that:
- Polls Camunda REST API for tasks matching its topic
- Executes business logic
- Completes or fails the task with appropriate variables
- Handles retries with exponential backoff
- Logs all actions with correlation IDs

**Integration Points:**
- Outbox table for transactional event publishing
- RabbitMQ topic (Publish): `product.offering.events`
- Synchronous HTTP calls to Specification Service and Pricing Service for ID validation before publication.
- Future: Camunda BPMN orchestration for the publication saga.

**Error Scenarios:**
- Invalid specification/pricing ID → 400 Bad Request
- Offering not in DRAFT for updates/deletion → 400 Bad Request
- Requirements for publication not met (min 1 spec, 1 price, 1 channel) → 400 Bad Request
- Specification/Pricing service unavailable → 503 Service Unavailable
- Not found → 404 Not Found

---

#### 3.2.5 Store Query Service (Read Service - CQRS)

**Bounded Context:** Sales Context  
**Databases:** 
- MongoDB (primary read store, denormalized documents)
- Elasticsearch (search index, aggregations)

**Responsibility:** Provide optimized read views for customer-facing catalog

**Data Model (MongoDB):**
- **PublishedOffering (Document)**
  ```
  {
    _id: UUID,
    name: string,
    description: string,
    specifications: [
      {
        id: UUID,
        name: string,
        characteristics: [
          { name: string, value: string, unit: string }
        ]
      }
    ],
    pricing: [
      { id: UUID, name: string, value: decimal, currency: string, unit: string }
    ],
    salesChannels: [string],
    publishedAt: timestamp,
    lifecycleStatus: "PUBLISHED",
    searchableText: string (concatenated for text search)
  }
  ```

**Data Synchronization:**
- **Event-Driven Updates:** Subscribe to RabbitMQ topics
  - `product.offerings.events` (OfferingPublished, OfferingRetired)
  - `resource.specifications.events` (SpecificationUpdated)
  - `resource.characteristics.events` (CharacteristicUpdated)
  - `commercial.pricing.events` (PriceUpdated)

- **Event Handlers:**
  - **On OfferingPublished:** 
    - Fetch full specification data from Specification Service (HTTP)
    - Fetch full pricing data from Pricing Service (HTTP)
    - Expand characteristic details for each spec
    - Create denormalized document in MongoDB
    - Index document in Elasticsearch
  
  - **On OfferingRetired:**
    - Remove from MongoDB
    - Remove from Elasticsearch index
  
  - **On SpecificationUpdated/CharacteristicUpdated:**
    - Find all offerings using this spec/characteristic
    - Re-fetch latest data
    - Update denormalized documents
    - Re-index in Elasticsearch
  
  - **On PriceUpdated:**
    - Find all offerings using this price
    - Update price information in documents
    - Re-index

**Idempotency:**
- Use event ID as idempotency key
- Store processed event IDs in separate collection
- Skip processing if event already handled

**API Endpoints:**
- GET /api/v1/store/offerings - List published offerings (pagination)
- GET /api/v1/store/offerings/{id} - Retrieve single offering with full details
- GET /api/v1/store/search - Search with filters and full-text query

**Search & Filtering Capabilities:**
- **Full-Text Search:** Query across name, description, characteristic values
- **Faceted Filtering:**
  - Price range (min/max)
  - Characteristics (e.g., speed >= 100 Mbps)
  - Multiple characteristics combined with AND/OR logic
- **Sorting:** By price, name, published date
- **Pagination:** Cursor-based or offset-based

**Elasticsearch Index Structure:**
```
{
  "mappings": {
    "properties": {
      "name": { "type": "text" },
      "description": { "type": "text" },
      "pricing.value": { "type": "scaled_float" },
      "characteristics.name": { "type": "keyword" },
      "characteristics.value": { "type": "keyword" },
      "characteristics.unit": { "type": "keyword" },
      "publishedAt": { "type": "date" }
    }
  }
}
```

**Query Example Requirements:**
- "Find all offerings with 'high-speed' in name, price less than 100 USD, and speed > 50 Mbps"
- Must support aggregations for facets (e.g., count by price range)

**Consistency Model:**
- **Eventual Consistency:** Acceptable lag between write and read (typically <1 second)
- No strong consistency guarantees required
- Display stale data temporarily is acceptable for customer-facing catalog

**Error Scenarios:**
- Source service unavailable during event processing → Retry with exponential backoff
- Elasticsearch indexing fails → Log error, continue with MongoDB (search degraded)
- Invalid event data → Dead-letter queue for manual inspection

---

#### 3.2.6 Identity Service

**Bounded Context:** Identity & Access Management  
**Database:** PostgreSQL (users schema) OR Keycloak (external)  
**Responsibility:** User authentication and JWT token issuance

**Two Implementation Options:**

**Option A: Custom JWT Service**
- Simple user table (id, username, password_hash, role)
- Hardcoded users for demo (admin/admin, user/user)
- JWT signing with RS256 algorithm
- Public key distribution to other services

**Option B: Keycloak Integration**
- Use Keycloak as identity provider
- OIDC/OAuth2 flows
- More production-ready but higher complexity

**Recommended:** Option A for term project simplicity

**Domain Model (Option A):**
- **User (Entity)**
  - Attributes: id (UUID), username (unique), passwordHash (bcrypt), role (enum: ADMIN, USER), createdAt

**API Endpoints:**
- POST /api/v1/auth/login - Authenticate and issue JWT
- POST /api/v1/auth/refresh - Refresh expired token (optional)
- GET /api/v1/auth/public-key - Provide public key for JWT verification

**JWT Token Structure:**
```json
{
  "sub": "user-id",
  "username": "admin",
  "role": "ADMIN",
  "iat": 1234567890,
  "exp": 1234571490
}
```

**Token Lifetime:** 1 hour (configurable)

**Security Requirements:**
- Password hashing: bcrypt with cost factor 12
- JWT signing: RS256 (asymmetric keys)
- Private key: Stored in Kubernetes secret or environment variable
- Public key: Exposed via endpoint for service validation

**Validation Logic (Shared Chassis):**
- Every service must validate JWT signature using public key
- Extract user ID and role from token
- Reject expired tokens
- No session state (stateless authentication)

---

#### 3.2.7 API Gateway

**Responsibility:** Single entry point for all client requests

**Core Functions:**
1. **Request Routing:** Forward requests to appropriate microservices
2. **Authentication:** Validate JWT on every request
3. **Circuit Breaking:** Prevent cascade failures
4. **Rate Limiting:** Protect services from overload (optional)
5. **Request/Response Transformation:** Aggregate responses if needed (API Composition pattern)
6. **CORS Handling:** Enable frontend cross-origin requests

**Routing Rules:**
```
/api/v1/auth/*          → Identity Service
/api/v1/characteristics/* → Characteristic Service
/api/v1/specifications/*  → Specification Service
/api/v1/prices/*          → Pricing Service
/api/v1/offerings/*       → Offering Service
/api/v1/store/*           → Store Query Service
```

**Circuit Breaker Configuration:**
- Failure threshold: 3 consecutive failures
- Open circuit duration: 20 seconds
- Half-open test requests: 3
- Apply per downstream service

**Timeout Policy:**
- Read timeout: 4 seconds
- Connection timeout: 2 seconds

**Error Handling:**
- 503 Service Unavailable if downstream unreachable
- Propagate 4xx errors from services
- Return user-friendly error messages (no stack traces)

**Headers Management:**
- Add correlation ID (X-Correlation-ID) if not present
- Forward Authorization header to services
- Add X-User-ID from JWT claims
- Inject trace context for Zipkin

**Health Check:**
- GET /health - Gateway own health
- GET /health/dependencies - Check downstream service health (circuit breaker status)

---

## 4. CROSS-CUTTING CONCERNS

### 4.1 Shared Chassis Library (libs/common-python)

**Purpose:** Eliminate code duplication across services

**Modules:**

#### 4.1.1 Logging Module
- Structured JSON logging (every log entry includes service name, timestamp, level, message)
- Correlation ID injection (thread-local or context variable)
- Integration with OpenTelemetry for trace context
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Output to stdout (Docker captures logs)

**Required Log Fields:**
```json
{
  "timestamp": "ISO8601",
  "level": "INFO",
  "service": "offering-service",
  "correlation_id": "uuid",
  "trace_id": "zipkin-trace-id",
  "message": "Offering published",
  "context": { additional fields }
}
```

#### 4.1.2 Security Module
- JWT verification utility using public key
- Extract claims (user_id, role)
- FastAPI dependency for protected routes
- Exception classes (UnauthorizedException, ForbiddenException)

**Usage Pattern:**
- Every protected endpoint must use authentication dependency
- Dependency validates token and injects user context
- Services trust Gateway validation but re-verify (zero-trust)

#### 4.1.3 Messaging Module
- RabbitMQ connection pool management
- Publisher wrapper (handles connection, retry, error logging)
- Consumer base class (auto-acknowledgment, error handling)
- Topic naming convention enforcement (context.entity.events)

**Publisher Interface:**
- `publish(topic: str, event: dict, correlation_id: str)`
- Automatic JSON serialization
- Retry on connection failure (3 attempts)
- Dead-letter queue configuration

**Consumer Interface:**
- Abstract base class with `handle_message(body: dict, headers: dict)` method
- Automatic acknowledgment on success
- Negative acknowledgment on exception (requeue)
- Idempotency check integration

#### 4.1.4 Outbox Module
- Outbox table model (id, topic, payload, status, created_at, processed_at, error_message)
- Postgres LISTEN/NOTIFY listener implementation with periodic polling fallback
- Background thread/task for event relay
- Status tracking (PENDING → SENT → FAILED)

**Outbox Pattern Implementation:**
- Every write service must have outbox table
- Database trigger on INSERT to outbox table fires NOTIFY
- Listener receives notification, fetches pending events
- Publishes to RabbitMQ, updates status to SENT
- Retry failed events with exponential backoff

**Postgres Trigger Example (Provided as SQL migration):**
```sql
CREATE OR REPLACE FUNCTION notify_outbox() RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify('outbox_events', NEW.id::text);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER outbox_notify AFTER INSERT ON outbox
FOR EACH ROW EXECUTE FUNCTION notify_outbox();
```

**Listener Pseudo-Logic:**
1. Connect to Postgres LISTEN channel
2. On notification received, fetch event by ID
3. Publish to RabbitMQ topic
4. Update status to SENT
5. Handle errors (log, retry later)

#### 4.1.6 Idempotency & Utility Module
- **Idempotency Decorator:** A reusable decorator for FastAPI routes and event handlers to track processed IDs.
- **Storage Adapter:** Interface for storing/checking idempotency keys (supporting Redis or SQL).
- **Version Comparison:** Utility to handle version-based update logic.

**Error Response Format:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Characteristic name is required",
    "details": { "field": "name" },
    "correlation_id": "uuid"
  }
}
```

---

### 4.2 Observability & Monitoring

#### 4.2.1 Distributed Tracing (Zipkin + OpenTelemetry)

**Requirements:**
- Every service must initialize OpenTelemetry SDK at startup
- Auto-instrumentation for FastAPI, HTTP clients, database calls
- Trace context propagated via HTTP headers (B3 format)
- Trace context propagated via RabbitMQ message headers
- Spans created for: HTTP requests, database queries, message publishing, Camunda task execution

**Span Naming Convention:**
- HTTP: `{method} {path}` (e.g., "POST /offerings")
- Database: `{operation} {table}` (e.g., "SELECT offerings")
- Messaging: `PUBLISH {topic}` or `CONSUME {queue}`
- Saga: `SAGA {process_name} {task_name}`

**Trace Visualization:**
- Zipkin UI must show complete request flow across services
- Latency breakdown per service
- Error traces highlighted

#### 4.2.2 Log Aggregation (ELK Stack)

**Architecture:**
- Services write JSON logs to stdout
- Docker captures logs
- Filebeat ships logs to Logstash
- Logstash parses and forwards to Elasticsearch
- Kibana provides UI for log search and visualization

**Kibana Dashboard Requirements:**
- Filter logs by service name
- Search by correlation ID (show all logs for one request)
- Error rate visualization (count of ERROR level logs per service)
- Latency graphs (extract from trace spans)

**Log Retention:** 7 days (configurable)

#### 4.2.3 Health Checks

**Service Health Endpoint:** GET /health

**Response Format:**
```json
{
  "status": "healthy",
  "database": "connected",
  "message_broker": "connected",
  "dependencies": {
    "specification_service": "healthy",
    "pricing_service": "degraded"
  }
}
```

**Status Values:**
- `healthy`: All systems operational
- `degraded`: Service operational but dependencies have issues
- `unhealthy`: Critical failure (database unreachable)

**Kubernetes Liveness/Readiness:**
- Liveness: Service process is alive
- Readiness: Service is ready to accept traffic (dependencies healthy)

#### 4.2.4 Metrics (Optional - Prometheus)

If time permits, expose Prometheus metrics:
- Request count (per endpoint, per status code)
- Request duration histogram
- Active connections (database, RabbitMQ)
- Circuit breaker state
- Event processing lag (Store Service)

---

### 4.3 Data Consistency & Integrity

#### 4.3.1 Database Transactions
- Every business operation that writes data must use database transactions
- Transactional Outbox ensures atomicity (business data + event in same transaction)
- Use optimistic locking (version field) for concurrent updates

#### 4.3.2 Event Schema Versioning
- All events must include schema version field
- Backward-compatible changes only (add optional fields)
- Consumers must handle unknown fields gracefully

**Event Structure:**
```json
{
  "event_id": "uuid",
  "event_type": "OfferingPublished",
  "schema_version": "1.0",
  "entity_version": 1,
  "timestamp": "ISO8601",
  "correlation_id": "uuid",
  "payload": { "domain-specific data" }
}
```

#### 4.3.3 Idempotency & Versioning
- **Event Versioning:** Every domain event must include a `version` (monotonically increasing) or a `sequence_number`.
- **Version-Based Concurrency:** The Store Query Service must implement **Version-based Optimistic Concurrency**. It shall compare the version of the incoming event with the version currently stored in the read-model.
- **Rules:**
  - If `incoming_version > stored_version`: Process event and update document.
  - If `incoming_version <= stored_version`: Ignore the event (stale/duplicate).
- **Idempotency Key:** Use `event_id` as a primary idempotency key.
- **Tracking:** Store processed event IDs and their associated entity versions in a tracking collection to prevent re-processing.

#### 4.3.4 Referential Integrity

**Enforcement Strategy:**
- **No foreign keys across services** (database-per-service)
- **Reference by ID only** (specification IDs, pricing IDs)
- **Validation via synchronous HTTP calls** before creation
- **Eventual consistency** via events for updates/deletes

**Cascading Delete Policy:**
Delete Policy:**
- Characteristic referenced by Specification → Reject delete
- Specification referenced by Offering → Reject delete
- Price locked by Saga → Reject delete
- Published/Retired Offering → No deletion (soft delete only)

---

### 4.4 Security & Authorization

#### 4.4.1 Zero Trust Model
- Every service validates JWT independently (no trust of Gateway)
- Public key fetched from Identity Service or shared via config
- Token expiration enforced
- No session state

#### 4.4.2 Role-Based Access Control (RBAC)

**Roles:**
- ADMIN: Full access (create, update, delete, publish)
- USER: Read-only access to all services, can create/update DRAFT offerings

**Authorization Rules:**
- Characteristic Service: Admin only for create/update/delete
- Specification Service: Admin only for create/update/delete
- Pricing Service: Admin only for create/update/delete
- Offering Service: Admin for publish/retire, User for draft operations
- Store Service: Public read access (no auth required)

**Implementation:**
- FastAPI dependency checks role from JWT claims
- Reject with 403 Forbidden if insufficient permissions

#### 4.4.3 Secure Communication
- All inter-service HTTP calls use service mesh mTLS (if deployed on Kubernetes with Istio)
- For Docker Compose: Services communicate within Docker network (not exposed to host)
- API Gateway is the only externally accessible endpoint

---

### 4.5 Service Discovery

**Development (Docker Compose):**
- Service names used as DNS hostnames
- Example: `http://pricing-service:8000`
- Docker Compose creates network, provides DNS resolution

**Production (Kubernetes):**
- Kubernetes CoreDNS provides service discovery
- Service name resolves to ClusterIP
- Example: `http://pricing-service.default.svc.cluster.local:8000`
- No hardcoded IPs
- No external service registry (Eureka, Consul) needed

**Configuration:**
- Service URLs provided via environment variables
- Format: `PRICING_SERVICE_URL=http://pricing-service:8000`
- Allows override for testing (point to mock services)

---

### 4.6 Resilience Patterns

#### 4.6.1 Circuit Breaker (API Gateway)
- Implemented using pybreaker library
- Configuration per downstream service
- Failure threshold: 3 failures
- Open duration: 20 seconds
- Half-open: Send test request, close if successful

**Fallback Behavior:**
- Return cached data if available
- Return partial response (exclude failed service data)
- Return 503 with retry-after header

#### 4.6.2 Retries with Exponential Backoff
- HTTP client retries: 3 attempts, exponential backoff (1s, 2s, 4s)
- Only retry on network errors or 5xx responses
- Do not retry on 4xx errors (client errors)
- Include jitter to prevent thundering herd

#### 4.6.3 Timeouts
- Connection timeout: 2 seconds
- Read timeout: 4 seconds
- Database query timeout: 5 seconds
- Message publishing timeout: 3 seconds

#### 4.6.4 Graceful Degradation
- If Store Service Elasticsearch unavailable, fall back to MongoDB (slower search)
- If Characteristic Service unavailable during Specification creation, fail fast (don't cache and retry)

---

## 5. TESTING REQUIREMENTS

### 5.1 Unit Tests

**Scope:** Domain logic (pure Python classes in domain layer)

**Coverage Target:** 80% of domain code

**Test Framework:** pytest

**Requirements:**
- Test all business rules (e.g., ProductOffering.canPublish())
- Test invariants (e.g., Characteristic cannot have empty name)
- Test state transitions (e.g., DRAFT → PUBLISHING → PUBLISHED)
- Mock external dependencies (repositories, message publishers)
- Fast execution (<1 second per test suite)

**Example Test Cases:**
- Characteristic creation with valid data succeeds
- Characteristic creation with invalid unit fails
- Specification creation without characteristics fails
- Offering publish validation with missing specs fails
- Offering state transition from PUBLISHED to RETIRED succeeds

---

### 5.2 Integration Tests

**Scope:** Repository layer, database interactions, message broker

**Test Framework:** pytest + Testcontainers

**Requirements:**
- Spin up real Postgres container for each test suite
- Spin up real RabbitMQ container for message tests
- Test database queries (CRUD operations)
- Test Outbox pattern (insert + trigger + listener)
- Test transaction rollback on error
- Clean database between tests

**Example Test Cases:**
- Insert Characteristic, verify it's retrievable
- Delete Specification referenced by Offering, verify constraint error
- Publish event to Outbox, verify it appears in RabbitMQ queue
- Concurrent update to same entity, verify optimistic locking

---

### 5.3 Component Tests

**Scope:** Single service in isolation (HTTP API)

**Test Framework:** pytest + httpx (FastAPI TestClient) + WireMock

**Requirements:**
- Test service REST API endpoints
- Mock external service HTTP calls using WireMock
- Verify request/response formats
- Test error handling (4xx, 5xx)
- Test authentication (valid/invalid JWT)

**Example Test Cases:**
- POST /specifications with valid data returns 201
- POST /specifications with non-existent characteristic ID returns 400
- PUT /offerings in PUBLISHED state returns 409
- GET /store/offerings returns paginated results

**WireMock Usage:**
- Start WireMock server in test setup
- Configure stubs for Characteristic Service, Pricing Service
- Point service under test to WireMock URL
- Verify service correctly handles responses

---

### 5.4 Contract Tests (Optional)

**Scope:** Verify API contracts between services

**Approach:** OpenAPI schema validation

**Requirements:**
- Each service exposes OpenAPI spec (FastAPI auto-generates)
- Validate request/response against schema
- Detect breaking changes (removed fields, changed types)

**Alternative:** Pact framework for consumer-driven contracts

---

### 5.5 End-to-End Tests

**Scope:** Complete user journeys through all services

**Test Framework:** pytest + requests

**Requirements:**
- Start all services via Docker Compose
- Execute real HTTP requests through API Gateway
- Verify data propagates across services
- Test saga completion (create offering, publish, verify in Store)
- Maximum 5 E2E test scenarios (test happy paths only)

**Example E2E Test:**
1. Login as admin, get JWT token
2. Create characteristic (Speed, 100, Mbps)
3. Create specification with characteristic ID
4. Create pricing ($50/month)
5. Create offering with spec and price
6. Publish offering (trigger saga)
7. Poll Store Service until offering appears
8. Verify offering details match
9. Retire offering
10. Verify offering removed from Store

**Execution Time:** <2 minutes for full E2E suite

---

### 5.6 Testing Checklist

Before declaring a service complete, verify:
- [ ] All domain business rules have unit tests
- [ ] Repository operations have integration tests
- [ ] All API endpoints have component tests
- [ ] Authentication and authorization tested
- [ ] Error scenarios covered (4xx, 5xx)
- [ ] At least one E2E test covering the service
- [ ] Outbox pattern verified with integration test
- [ ] Event publishing/consuming tested
- [ ] Circuit breaker behavior tested (Gateway)
- [ ] Saga compensation tested (Offering Service)

---

## 6. DEPLOYMENT & INFRASTRUCTURE

### 6.1 Docker Compose (Development)

**Services to Run:**
- postgres (shared for all write services)
- mongodb (Store Service)
- elasticsearch + kibana (Store Service search)
- rabbitmq (management UI enabled)
- zipkin (tracing UI)
- camunda (workflow engine, H2 or Postgres)
- keycloak (optional, if using external identity)

**Service Containers:**
- api-gateway (port 8000 exposed to host)
- identity-service (internal only)
- characteristic-service (internal only)
- specification-service (internal only)
- pricing-service (internal only)
- offering-service (internal only)
- store-service (internal only)

**Networking:**
- Single Docker network
- Services communicate by service name
- Only Gateway port exposed externally

**Environment Variables (per service):**
- `DATABASE_URL`: Postgres connection string
- `RABBITMQ_URL`: amqp://rabbitmq:5672
- `ZIPKIN_URL`: http://zipkin:9411
- `JWT_PUBLIC_KEY_URL`: http://identity-service:8000/auth/public-key
- `LOG_LEVEL`: INFO
- Service-specific URLs (CHARACTERISTIC_SERVICE_URL, etc.)

**Health Check Dependencies:**
- Services depend on Postgres, RabbitMQ being healthy before starting
- Use Docker Compose healthcheck and depends_on conditions

---

### 6.2 Database Migrations

**Tool:** Alembic (Python SQL migration tool)

**Requirements:**
- Each service maintains its own Alembic migration folder
- Migrations run automatically on service startup (or via init container)
- Include migrations for:
  - Entity tables (characteristics, specifications, prices, offerings, users)
  - Outbox table
  - Indexes (name uniqueness, foreign key indexes)
  - Triggers (NOTIFY on Outbox insert)

**Migration Naming:** Sequential version numbers (001_initial.py, 002_add_version_field.py)

---

### 6.3 Configuration Management

**Strategy:** Environment variables (12-factor app)

**No Hardcoded Values:**
- Database credentials
- Service URLs
- JWT keys
- RabbitMQ connection strings

**Configuration Sources:**
- Docker Compose .env file (development)
- Kubernetes ConfigMaps and Secrets (production)

**Sensitive Data:**
- JWT private key: Kubernetes Secret or vault
- Database passwords: Kubernetes Secret
- Never commit secrets to Git

---

### 6.4 Kubernetes Readiness (Future)

**While not required for term project, design should support:**
- Horizontal Pod Autoscaler (HPA) for each service
- Liveness and readiness probes (/health endpoint)
- Resource limits (CPU, memory requests/limits)
- Service mesh (Istio) for mTLS, observability
- Persistent volumes for databases (StatefulSets)
- Ingress controller (NGINX) for external access

---

## 7. CAMUNDA SAGA IMPLEMENTATION DETAILS

### 7.1 BPMN Process Definition

**Process ID:** `offering-publication-saga`

**Process Variables (Input):**
- `offeringId` (UUID)
- `specificationIds` (List[UUID])
- `pricingIds` (List[UUID])
- `correlationId` (string)

**Service Tasks:**

1. **Lock Prices**
   - Type: External Task
   - Topic: `lock-prices`
   - Worker: Pricing Service
   - Input: `pricingIds`
   - Output: `lockResult` (boolean)

2. **Validate Specifications**
   - Type: External Task
   - Topic: `validate-specifications`
   - Worker: Specification Service
   - Input: `specificationIds`
   - Output: `validationResult` (boolean)

3. **Create Store Entry**
   - Type: External Task
   - Topic: `create-store-entry`
   - Worker: Store Service
   - Input: `offeringId`, `specificationIds`, `pricingIds`
   - Output: `storeEntryId` (UUID)

4. **Confirm Publication**
   - Type: External Task
   - Topic: `confirm-publication`
   - Worker: Offering Service
   - Input: `offeringId`
   - Output: `publishedAt` (timestamp)

**Error Handling:**
- Each task has retry configuration (3 retries, exponential backoff)
- If task exhausts retries, trigger compensation flow

**Compensation Flow:**
- Unlock Prices (call Pricing Service)
- Delete Store Entry (call Store Service)
- Revert Offering to DRAFT (call Offering Service)
- End process with failure

---

### 7.2 External Task Worker Pattern

**Implementation Requirements (per service):**

**Worker Lifecycle:**
1. On service startup, initialize Camunda client
2. Register worker with specific topic name
3. Poll Camunda REST API for tasks (long-polling, 30 second timeout)
4. On task received:
   - Extract process variables
   - Execute business logic
   - Complete task with output variables OR fail with error message
5. Handle worker shutdown gracefully (finish in-flight tasks)

**Python Pseudo-Implementation:**
```python
# Using camunda-external-task-client-python library

from camunda.external_task.external_task_worker import ExternalTaskWorker

worker = ExternalTaskWorker("pricing-service-worker")

@worker.subscribe("lock-prices")
def lock_prices_handler(task):
    pricing_ids = task.get_variable("pricingIds")
    correlation_id = task.get_variable("correlationId")
    
    # Business logic
    try:
        for price_id in pricing_ids:
            pricing_service.lock_price(price_id, correlation_id)
        
        return task.complete({"lockResult": True})
    
    except Exception as e:
        return task.failure(
            error_message=str(e),
            error_details="Failed to lock prices",
            retries=3,
            retry_timeout=5000
        )

worker.start()
```

**Worker Configuration:**
- Camunda REST API URL: `http://camunda:8080/engine-rest`
- Poll interval: 1 seconds
- Max tasks per poll: 10
- Lock duration: 60 seconds (prevent duplicate execution)

---

### 7.3 Saga Monitoring

**Camunda Cockpit Usage:**
- View running process instances
- See which task is currently executing
- Inspect process variables
- View incident reports (failed tasks)
- Manually retry failed tasks (useful for demo recovery)

**Logging Requirements:**
- Log saga start with correlation ID
- Log each task execution (start, complete, fail)
- Log compensation trigger
- Log saga completion

**Tracing Integration:**
- Pass Zipkin trace context as process variable
- Workers inject trace context when making HTTP calls
- Entire saga visible as single distributed trace

---

## 8. DATA MODELS & SCHEMAS

### 8.1 Database Schemas (PostgreSQL)

**Characteristic Service:**
```sql
CREATE TABLE characteristics (
    id UUID PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    value VARCHAR(100) NOT NULL,
    unit_of_measure VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE outbox (
    id UUID PRIMARY KEY,
    topic VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    error_message TEXT
);

CREATE INDEX idx_outbox_status ON outbox(status) WHERE status = 'PENDING';
```

**Specification Service:**
```sql
CREATE TABLE specifications (
    id UUID PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    characteristic_ids UUID[] NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Local Cache for Characteristics (Validation Autonomy)
CREATE TABLE cached_characteristics (
    id UUID PRIMARY KEY,
    name VARCHAR(200),
    last_updated_at TIMESTAMP DEFAULT NOW()
);

-- Outbox table same as above
```

**Pricing Service:**
```sql
CREATE TABLE prices (
    id UUID PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    value DECIMAL(10,2) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    locked BOOLEAN DEFAULT FALSE,
    locked_by_saga_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE outbox (
    id UUID PRIMARY KEY,
    topic VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    error_message TEXT
);

CREATE INDEX idx_prices_name ON prices(name);
CREATE INDEX idx_outbox_status_pricing ON outbox(status) WHERE status = 'PENDING';
```

**Offering Service:**
```sql
CREATE TABLE product_offerings (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    specification_ids UUID[] NOT NULL,
    pricing_ids UUID[] NOT NULL,
    sales_channels VARCHAR(50)[] NOT NULL,
    lifecycle_status VARCHAR(20) NOT NULL,
    published_at TIMESTAMP,
    retired_at TIMESTAMP,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_lifecycle_status ON product_offerings(lifecycle_status);

-- Outbox table
```

**Identity Service:**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### 8.2 Event Schemas (RabbitMQ)

**Characteristic Events:**
```json
{
  "event_id": "uuid",
  "event_type": "CharacteristicCreated",
  "schema_version": "1.0",
  "entity_version": 1,
  "timestamp": "2026-01-15T10:30:00Z",
  "correlation_id": "uuid",
  "payload": {
    "id": "uuid",
    "name": "Speed",
    "value": "100",
    "unit_of_measure": "Mbps"
  }
}
```

**Specification Events:**
```json
{
  "event_type": "SpecificationCreated",
  "event_id": "uuid",
  "schema_version": "1.0",
  "entity_version": 1,
  "timestamp": "...",
  "payload": {
    "id": "uuid",
    "name": "High-Speed Internet Package",
    "characteristic_ids": ["uuid1", "uuid2"]
  }
}
```

**Offering Events:**
```json
{
  "event_type": "OfferingPublished",
  "event_id": "uuid",
  "schema_version": "1.0",
  "entity_version": 1,
  "timestamp": "...",
  "payload": {
    "id": "uuid",
    "name": "Premium Package",
    "specification_ids": ["uuid"],
    "pricing_ids": ["uuid"],
    "sales_channels": ["online"],
    "published_at": "2026-01-15T11:00:00Z"
  }
}
```

---

### 8.3 API Request/Response Schemas

**Create Characteristic Request:**
```json
POST /api/v1/characteristics
{
  "name": "Speed",
  "value": "100",
  "unit_of_measure": "Mbps"
}
```

**Response:**
```json
201 Created
{
  "id": "uuid",
  "name": "Speed",
  "value": "100",
  "unit_of_measure": "Mbps",
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z"
}
```

**Create Specification Request:**
```json
POST /api/v1/specifications
{
  "name": "High-Speed Package",
  "characteristic_ids": ["uuid1", "uuid2"]
}
```

**Publish Offering Request:**
```json
POST /api/v1/offerings/{id}/publish
{}
```

**Response (Saga Initiated):**
```json
202 Accepted
{
  "message": "Publication saga initiated",
  "saga_id": "camunda-process-id",
  "offering_id": "uuid",
  "status": "PUBLISHING"
}
```

**Store Search Request:**
```json
GET /api/v1/store/offerings?query=high-speed&min_price=10&max_price=100&characteristic=Speed:>50Mbps
```

**Response:**
```json
{
  "total": 25,
  "page": 1,
  "page_size": 10,
  "items": [
    {
      "id": "uuid",
      "name": "Premium Package",
      "specifications": [...],
      "pricing": [...],
      "published_at": "..."
    }
  ],
  "facets": {
    "price_ranges": [
      {"range": "0-50", "count": 10},
      {"range": "50-100", "count": 15}
    ]
  }
}
```

---

## 9. BUSINESS RULES SUMMARY

### 9.1 Characteristic Business Rules
1. Name must be unique across all characteristics
2. Unit of measure must be from enum (Mbps, Gbps, MB, GB, TB, GHz, Volt, Watt, Meter, Percent, Seconds, Minutes, Hours, Days, Months, Years, Unit, None)
3. Cannot be deleted if referenced by any specification
4. Updates must propagate to dependent specifications via events

### 9.2 Specification Business Rules
1. Must contain at least one characteristic reference
2. All characteristic IDs must exist (validated synchronously)
3. Name must be unique
4. Cannot be deleted if referenced by any product offering
5. When characteristic is updated, specification view is eventually consistent

### 9.3 Pricing Business Rules
1. Value must be positive decimal with 2 decimal places
2. Currency must be valid ISO code (USD, EUR, TRY)
3. Can be locked during saga execution
4. Locked prices cannot be deleted or modified
5. Saga failure automatically unlocks prices

### 9.4 Product Offering Business Rules
1. Can be created in DRAFT state with only name (partial entity)
2. To publish, must have: at least one spec, one price, one sales channel
3. Published offerings are immutable (cannot be edited)
4. Only PUBLISHED offerings can transition to RETIRED
5. RETIRED offerings hidden from Store but remain in database
6. DRAFT offerings can be deleted, PUBLISHED/RETIRED cannot
7. Publication triggers Camunda saga with compensation on failure

### 9.5 Store Query Business Rules
1. Only PUBLISHED offerings visible in Store
2. Data is eventually consistent (acceptable lag <1 second)
3. Search must support full-text, filters, facets, sorting
4. Retired offerings immediately removed from index

### 9.6 Cross-Cutting Business Rules
1. All entities have UUIDs (not sequential IDs for security)
2. All timestamps in UTC ISO 8601 format
3. Soft deletes for audit trail (where applicable)
4. Optimistic locking prevents concurrent update conflicts
5. Every operation must have correlation ID for tracing

---

## 10. NON-FUNCTIONAL REQUIREMENTS

### 10.1 Performance
- API response time: <200ms for read operations (p95)
- API response time: <500ms for write operations (p95)
- Store search: <100ms for simple queries (p95)
- Event processing lag: <1 second (p95)
- Support 100 concurrent users (sufficient for demo)

### 10.2 Scalability
- Each service independently scalable (horizontal)
- Database per service prevents bottlenecks
- Stateless services (no session affinity)
- Message broker supports backpressure

### 10.3 Reliability
- Target uptime: 99% (acceptable for term project)
- Circuit breakers prevent cascade failures
- Retries with exponential backoff
- Saga compensation ensures consistency
- Database transactions prevent partial writes

### 10.4 Security
- All endpoints except health checks require authentication
- JWT tokens expire after 1 hour
- Passwords hashed with bcrypt (cost 12)
- No sensitive data in logs
- HTTPS in production (not enforced in Docker Compose)

### 10.5 Maintainability
- Clean Architecture (domain decoupled from infrastructure)
- Shared chassis reduces duplication
- Comprehensive logging for debugging
- OpenAPI documentation auto-generated
- Test coverage >70%

### 10.6 Observability
- Distributed tracing covers 100% of requests
- Structured JSON logging
- Correlation IDs link logs across services
- Health checks for all dependencies
- Saga execution visible in Camunda Cockpit

---

## 11. DEVELOPMENT WORKFLOW

### 11.1 Service Implementation Phases

**Phase 1: Infrastructure Setup (Week 1)**
- Create monorepo structure
- Set up Docker Compose with all infrastructure services
- Implement shared chassis library (logging, security, messaging, outbox)
- Create database migration scripts

**Phase 2: Core Write Services (Week 2)**
- Implement Characteristic Service (domain, API, outbox)
- Implement Specification Service (domain, API, cross-service validation)
- Implement Pricing Service (domain, API, locking mechanism)
- Write unit and integration tests for each

**Phase 3: Offering Service & Saga (Week 2-3)**
- Implement Offering Service domain model
- Create Camunda BPMN process definition
- Implement External Task workers in each service
- Test saga happy path and compensation flow

**Phase 4: Read Services (Week 3)**
- Implement Store Query Service
- Set up MongoDB and Elasticsearch
- Implement event consumers for data synchronization
- Test search and filtering

**Phase 5: Gateway & Security (Week 3)**
- Implement API Gateway with routing
- Implement Identity Service (JWT issuance)
- Add authentication to all services
- Implement circuit breakers

**Phase 6: Observability (Week 4)**
- Configure OpenTelemetry in all services
- Set up Zipkin and verify traces
- Configure ELK stack
- Create Kibana dashboards

**Phase 7: Frontend (Week 4)**
- Implement Next.js UI (Builder, Viewer, Store pages)
- Integrate with API Gateway
- Test end-to-end user flows

**Phase 8: Testing & Documentation (Week 4)**
- Write remaining tests (component, E2E)
- Create architecture diagrams
- Write project report
- Prepare demo video

---

### 11.2 Git Workflow (Monorepo)

**Branch Strategy:**
- `main`: Stable code, always deployable
- `develop`: Integration branch
- Feature branches: `feature/characteristic-service`, `feature/saga`

**Commit Messages:**
- Follow conventional commits format
- Example: `feat(offering): implement publish saga orchestration`

**Pull Request Requirements:**
- Tests passing
- Code review (if team project)
- No merge conflicts

---

### 11.3 Local Development

**Starting Services:**
```bash
# Start infrastructure only
docker-compose up -d postgres rabbitmq mongodb elasticsearch zipkin camunda

# Run service locally for development
cd services/characteristic-service
uv run uvicorn src.main:app --reload --port 8002

# For Pricing Service (uses internal module naming)
cd services/pricing-service
uv run uvicorn pricing.main:app --reload --port 8004

# For Offering Service (uses internal module naming)
cd services/offering-service
uv run uvicorn offering.main:app --reload --port 8005

# For Store Service (uses internal module naming)
cd services/store-service
uv run uvicorn store.main:app --reload --port 8006

# Run all services
docker-compose up
```

**Database Migrations:**
```bash
cd services/characteristic-service
uv run alembic upgrade head
```

**Testing:**
```bash
# Unit tests
uv run pytest tests/unit

# Integration tests (requires Docker)
uv run pytest tests/integration

# E2E tests (requires all services running)
uv run pytest tests/e2e
```

---

## 12. SUCCESS CRITERIA

The backend system is considered complete when:

1. ✅ All 6 microservices are implemented and running
2. ✅ Database-per-service pattern enforced (no shared databases)
3. ✅ API Gateway routes requests to appropriate services
4. ✅ Authentication works (JWT validation at Gateway and services)
5. ✅ Characteristic, Specification, Pricing services support full CRUD
6. ✅ Product Offering service implements lifecycle state machine
7. ✅ Publication saga orchestrated by Camunda with compensation
8. ✅ Transactional Outbox with Postgres LISTEN/NOTIFY implemented
9. ✅ Events published to RabbitMQ for all domain changes
10. ✅ Store Query Service consumes events and builds read model
11. ✅ Store Service provides search with Elasticsearch
12. ✅ Circuit breaker prevents cascade failures
13. ✅ Distributed tracing shows complete request flow in Zipkin
14. ✅ Logs aggregated in Elasticsearch, searchable by correlation ID
15. ✅ Unit tests cover domain logic (>70% coverage)
16. ✅ Integration tests verify database and messaging
17. ✅ At least one E2E test covers complete user journey
18. ✅ Health checks implemented for all services
19. ✅ All services start via Docker Compose without errors
20. ✅ Demo scenario executable: create entities → publish offering → verify in Store

---

## 13. POTENTIAL CHALLENGES & MITIGATION

### Challenge 1: Camunda Worker Coordination
**Risk:** Workers polling too frequently or missing tasks  
**Mitigation:** Configure appropriate poll intervals (1s), lock duration (60s), and retry policies

### Challenge 2: Event Processing Lag
**Risk:** Store Service falls behind on event processing  
**Mitigation:** Implement monitoring of queue depth, add backpressure handling, consider multiple consumer instances

### Challenge 3: Circular Dependencies
**Risk:** Service A calls Service B, Service B calls Service A  
**Mitigation:** Enforce unidirectional dependencies (Offering → Spec/Price, never reverse), use events for bidirectional communication

### Challenge 4: Transaction Boundaries
**Risk:** Forgetting to include Outbox insert in same transaction  
**Mitigation:** Use shared chassis pattern, enforce in code reviews, write integration tests

### Challenge 5: Debugging Distributed Transactions
**Risk:** Saga failure hard to diagnose  
**Mitigation:** Comprehensive logging with correlation IDs, Camunda Cockpit visualization, Zipkin traces

### Challenge 6: Docker Compose Resource Limits
**Risk:** Running out of memory with 13 containers  
**Mitigation:** Allocate sufficient Docker resources (8GB RAM minimum), disable unnecessary services during development

### Challenge 7: Test Data Management
**Risk:** Stale test data causing false positives  
**Mitigation:** Use Testcontainers for clean database per test, implement database reset scripts

### Challenge 8: Time Management
**Risk:** Overengineering and missing deadline  
**Mitigation:** Implement MVP first (Phase 0: basic CRUD without Camunda/Elastic), add advanced features incrementally

---

## 14. ARCHITECTURAL TRADE-OFFS JUSTIFICATION

### Trade-off 1: Monorepo vs Polyrepo
**Decision:** Monorepo  
**Trade-off:** Less realistic isolation vs easier development  
**Justification:** Solo developer, AI agent workflow, shared chassis benefits outweigh independence concerns

### Trade-off 2: RabbitMQ vs Kafka
**Decision:** RabbitMQ  
**Trade-off:** Simpler setup vs event sourcing capabilities  
**Justification:** Sufficient for term project, faster to implement, still demonstrates async messaging patterns

### Trade-off 3: Custom JWT vs Keycloak
**Decision:** Custom JWT Service  
**Trade-off:** Less production-ready vs lower complexity  
**Justification:** Demonstrates understanding of JWT without external dependency overhead

### Trade-off 4: Saga Orchestration (Camunda) vs Choreography
**Decision:** Orchestration  
**Trade-off:** Central point of failure vs visibility  
**Justification:** Easier to understand, debug, and demonstrate in project report and video

### Trade-off 5: Eventual Consistency (CQRS) vs Strong Consistency
**Decision:** Eventual Consistency for Store  
**Trade-off:** Stale reads vs scalability  
**Justification:** Acceptable for customer-facing catalog, demonstrates CQRS pattern understanding

### Trade-off 6: Postgres LISTEN/NOTIFY vs Kafka Connect
**Decision:** Postgres LISTEN/NOTIFY  
**Trade-off:** Postgres coupling vs simpler architecture  
**Justification:** Native Postgres feature, real-time performance, eliminates Kafka dependency for Outbox

### Trade-off 7: Full E2E Tests vs Component Tests
**Decision:** Minimal E2E, comprehensive component tests  
**Trade-off:** Coverage vs execution speed  
**Justification:** Component tests are faster, more reliable, E2E tests brittle in microservices

### Trade-off 8: Elasticsearch vs MongoDB-Only
**Decision:** Add Elasticsearch  
**Trade-off:** Complexity vs search capabilities  
**Justification:** Demonstrates understanding of polyglot persistence, realistic for catalog search requirements

---

## APPENDICES

### Appendix A: Glossary

- **Aggregate Root:** The main entity in a DDD aggregate that enforces invariants
- **Bounded Context:** A logical boundary defining where a domain model applies
- **Circuit Breaker:** Resilience pattern that fails fast when service is unavailable
- **Correlation ID:** Unique identifier linking logs and traces across services
- **CQRS:** Command Query Responsibility Segregation (separate read and write models)
- **Idempotency:** Operation that produces same result when executed multiple times
- **Outbox Pattern:** Transactional pattern ensuring atomic database write and event publish
- **Saga:** Distributed transaction pattern with compensating transactions
- **Testcontainers:** Library for running Docker containers in integration tests

### Appendix B: Technology Versions

- Python: 3.12+
- FastAPI: 0.104+
- PostgreSQL: 15+
- MongoDB: 7+
- Elasticsearch: 8.11+
- RabbitMQ: 3.12+
- Camunda: 7.20+
- Zipkin: 2.24+
- Docker: 24+
- Docker Compose: 2.20+

### Appendix C: Port Assignments (Docker Compose)

- API Gateway: 8000
- Identity Service: 8001 (internal)
- Characteristic Service: 8002 (internal)
- Specification Service: 8003 (internal)
- Pricing Service: 8004 (internal)
- - Offering Service: 8005 (internal)
- Store Service: 8006 (internal)
- PostgreSQL: 5432
- MongoDB: 27017
- Elasticsearch: 9200
- Kibana: 5601
- RabbitMQ: 5672 (AMQP), 15672 (Management UI)
- Zipkin: 9411
- Camunda: 8085 (Cockpit UI)

### Appendix D: Environment Variables Template

```bash
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/service_db
MONGODB_URL=mongodb://mongodb:27017/store_db
ELASTICSEARCH_URL=http://elasticsearch:9200

# Messaging
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672

# Observability
ZIPKIN_URL=http://zipkin:9411
LOG_LEVEL=INFO

# Security
JWT_PUBLIC_KEY_URL=http://identity-service:8001/api/v1/auth/public-key
JWT_PRIVATE_KEY=<base64-encoded-private-key>

# Service Discovery
CHARACTERISTIC_SERVICE_URL=http://characteristic-service:8002
SPECIFICATION_SERVICE_URL=http://specification-service:8003
PRICING_SERVICE_URL=http://pricing-service:8004
OFFERING_SERVICE_URL=http://offering-service:8005
STORE_SERVICE_URL=http://store-service:8006

# Camunda
CAMUNDA_URL=http://camunda:8080/engine-rest

# Application
SERVICE_NAME=characteristic-service
PORT=8002
```

### Appendix E: RabbitMQ Topic Naming Convention

- Characteristic Events: `resource.characteristics.events`
- Specification Events: `resource.specifications.events`
- Pricing Events: `commercial.pricing.events`
- Offering Events: `product.offerings.events`
- Store Events: `sales.store.events` (if needed)

Exchange Type: **Topic Exchange** (allows pattern-based routing)

Queue Naming: `{service-name}.{event-type}.queue`
- Example: `store-service.offering-published.queue`

---