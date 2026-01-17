Here is your **Incremental Roadmap**.

---

## PART I: BACKEND INFRASTRUCTURE & CORE (The Foundation)

### Phase 1: The Monorepo Skeleton & Infrastructure

**Goal:** Establish the physical environment where code lives and runs.

*   Initialize the `uv` monorepo workspace and Git repository.
*   Create the master `docker-compose.yml` defining all infrastructure:
    *   PostgreSQL 15+ (Write databases)
    *   RabbitMQ (Message broker with Management UI)
    *   MongoDB 7+ (Read store for CQRS)
    *   Elasticsearch 8+ (Search index)
    *   Camunda 7 (BPMN workflow engine)
    *   Zipkin (Distributed tracing)
    *   ELK Stack (Elasticsearch, Logstash, Kibana for log aggregation)
*   Create a simple health check service to verify infrastructure connectivity.
*   **Verification:** `docker-compose up` runs without exiting. All services healthy. RabbitMQ Management UI accessible at :15672.

**Status Update (Jan 10, 2026):**
*   **Monorepo Initialized:** `uv` workspace configured with `services/` and `libs/` directories.
*   **Infrastructure Ready:** `docker-compose.yml` orchestrates 8 services (Postgres, RabbitMQ, Mongo, ES, Camunda, Zipkin, Logstash, Kibana).
*   **DB Setup:** Single Postgres container configured with `init-db.sql` to provision 5 microservice databases.
*   **Connectivity:** `scripts/check_infra.py` implemented to verify port availability across the stack.
*   **Configuration:** Camunda port shifted to `:8085` to resolve local environment conflicts.

### Phase 2: The Shared Chassis (Library)

**Goal:** Define *how* code is written so we don't repeat ourselves.

*   Create `libs/common-python`.
*   Implement standard **Structured Logging** (JSON format with service name, timestamp, level, correlation_id, trace_id).
*   Implement **Configuration Management** (Pydantic settings reading from environment variables).
*   Implement the **Standard Exception Hierarchy**:
    *   `ValidationError` → 400 Bad Request
    *   `NotFoundError` → 404 Not Found
    *   `ConflictError` → 409 Conflict
    *   `ServiceUnavailableError` → 503 Service Unavailable
*   **Idempotency & Versioning Utilities:**
    *   Implement idempotency decorator for route handlers.
    *   Implement version comparison logic for optimistic concurrency.
*   Implement standard **Error Response Format** with correlation ID.
*   **Verification:** Write unit tests in the library that log a JSON message and handle custom exceptions correctly.

**Status Update (Jan 10, 2026):**
*   **Library Initialized:** `libs/common-python` created as a `uv` package.
*   **Logging:** Structured JSON logging implemented with `service_name`, `correlation_id`, and `trace_id` support.
*   **Configuration:** `BaseServiceSettings` using Pydantic Settings implemented for environment-based config.
*   **Exceptions & Schemas:** Standardized `AppException` hierarchy and `ErrorResponse` schemas established.
*   **Utilities:** Versioning (OCC) and Idempotency decorator skeletons added.
*   **Verified:** Unit tests passed for logging, config, exceptions, and utilities.

### Phase 3: Identity & Security (Zero Trust)

**Goal:** Secure the system before building business logic.

*   Implement the **Identity Service** (Custom JWT Service - Option A for simplicity):
    *   User table (id, username, password_hash, role)
    *   Hardcoded users for demo: admin/admin (ADMIN role), user/user (USER role)
    *   Password hashing with bcrypt (cost factor 12)
    *   JWT signing with RS256 (asymmetric keys)
    *   Token lifetime: 1 hour
*   Define the **JWT Schema** (sub, username, role, iat, exp).
*   Expose `GET /api/v1/auth/public-key` for other services.
*   Update `common-python` Chassis with:
    *   `verify_jwt` FastAPI dependency
    *   Role-based authorization helpers
    *   `UnauthorizedException` and `ForbiddenException`
*   **Verification:** 
    *   `POST /api/v1/auth/login` returns JWT token.
    *   Protected endpoint returns 401 without token.
    *   Protected endpoint returns 200 with valid token.
    *   Admin-only endpoint returns 403 for USER role.

**Status Update (Jan 10, 2026):**
*   **Identity Service Implemented:** FastAPI service with SQLAlchemy/PostgreSQL storage.
*   **Zero Trust Security:** RS256 JWT signing with asymmetric keys implemented.
*   **Database:** User model established; demo users seeded.
*   **Shared Security:** `common-python` updated with `get_current_user` and `RoleChecker` dependencies.
*   **Management:** `scripts/generate_keys.sh` created for local RSA key generation; keys excluded from Git.
*   **Verified:** Login flow and token generation tested and working.

### Phase 4: Database Migrations Setup

**Goal:** Establish database schema management with Alembic.

*   Set up Alembic for each service's database schema.
*   Create initial migration scripts for Identity Service.
*   Establish migration patterns for the monorepo (per-service migrations).
*   **Verification:** `alembic upgrade head` creates tables. `alembic downgrade -1` rolls back.

**Status Update (Jan 10, 2026):**
*   **Centralized Migration Engine:** Shared migration logic moved to `libs/common-python` to ensure consistency across services.
*   **Monorepo Tooling:** Implemented `scripts/migrate.py` to manage migrations for all services from the project root.
*   **Refactored Identity:** Updated `identity-service` to use the shared engine, keeping its `env.py` clean and maintainable.
*   **Verified:** Global workflow tested successfully with `upgrade`, `downgrade`, and `history` commands.

---

## PART II: DOMAIN IMPLEMENTATION (Clean Architecture)

### Phase 5: The First Vertical Slice (Characteristic Service)

**Goal:** Establish the pattern for **Clean Architecture** (Domain → Application → Infrastructure).

*   Implement `Characteristic Service` (Write side).
*   Structure:
    *   **Domain Layer:** `Characteristic` entity with business rules (name unique, valid unit enum).
    *   **Application Layer:** Use cases (CreateCharacteristic, UpdateCharacteristic, DeleteCharacteristic).
    *   **Infrastructure Layer:** SQLAlchemy repository, FastAPI routes.
*   Define Pydantic DTOs for API request/response.
*   Implement validation rules:
    *   Name: Required, 1-200 characters, alphanumeric with spaces
    *   Value: Required, 1-100 characters
    *   UnitOfMeasure: Required, enum [Mbps, GB, GHz, Volt, Watt, Meter, None, and many many more enums]
*   Implement Health Check endpoint: `GET /health`.
*   **Crucial:** Do **NOT** implement Outbox or RabbitMQ yet. Just pure CRUD.
*   **Verification:** 
    *   `pytest` passes for Domain logic (business rules, validation).
    *   `curl` to create, read, update, delete a Characteristic.
    *   Duplicate name returns 409 Conflict.
    *   **Status Update (Jan 10, 2026):**
        *   **Characteristic Service Implemented:** Established Clean Architecture pattern (Domain -> Application -> Infrastructure).
        *   **Data Consistency:** Unique name constraints and unit validation enforced.
        *   **Security:** Integrated with `common-python` security module for JWT/RBAC.
        *   **Verified:** Comprehensive test suite implemented (Unit, Integration, and Component tests) with 100% pass rate.

### Phase 6: The Event Engine (Transactional Outbox)

**Goal:** Enable reliable async messaging without breaking the DB transaction.

*   Extend `common-python` with:
    *   **Outbox Table Model** (id, topic, payload, status, created_at).
    *   **Postgres LISTEN/NOTIFY** listener (background thread/asyncio task).
    *   **RabbitMQ Publisher** wrapper with retry logic (3 attempts, exponential backoff).
    *   **Event Schema** with version, event_id, event_type, timestamp, correlation_id, payload.
*   Create SQL migration for Outbox table with trigger:
    ```sql
    CREATE TRIGGER outbox_notify AFTER INSERT ON outbox
    FOR EACH ROW EXECUTE FUNCTION notify_outbox();
    ```
*   Update `Characteristic Service` to:
    *   Write to Outbox on create → `CharacteristicCreated`
    *   Write to Outbox on update → `CharacteristicUpdated`
    *   Write to Outbox on delete → `CharacteristicDeleted`
*   **Verification:** 
    *   Create a Characteristic via API.
    *   Check Postgres `outbox` table (status: SENT).
    *   Check RabbitMQ Management UI for message in `resource.characteristics.events` queue.
*   **Status Update (Jan 16, 2026):**
    *   **Event Engine Implemented:** Extended `common-python` with `Event` schemas, `RabbitMQPublisher`, and `OutboxListener`.
    *   **Reliability:** Implemented Transactional Outbox pattern using Postgres triggers and LISTEN/NOTIFY for real-time event processing with periodic polling fallback.
    *   **Integration:** Updated `CharacteristicService` to atomically persist domain events (`CharacteristicCreated`, `Updated`, `Deleted`) alongside business data.
    *   **Verified:** Full E2E outbox flow tested: API call -> Outbox record (PENDING) -> Listener -> RabbitMQ -> Outbox record (SENT).

### Phase 7: Dependency Management (Specification Service)

**Goal:** Handle cross-service dependencies with Eventual Consistency.

*   Implement `Specification Service` (Write side) following same Clean Architecture.
*   **Implement Local Reference Cache:**
    *   Create `cached_characteristics` table (id, valid_until).
    *   Subscribe to `resource.characteristics.events` (RabbitMQ consumer).
    *   On `CharacteristicCreated` / `Updated`: Upsert into cache.
    *   On `CharacteristicDeleted`: Remove from cache.
*   **Update Validation Logic:**
    *   Validate Characteristic IDs against local `cached_characteristics` table.
    *   If ID missing, return 400 (or optional: implement lazy-load fallback with Circuit Breaker).
*   Implement Domain Logic:
    *   "A spec must have at least 1 characteristic."
    *   "Name must be unique."
    *   "Cannot delete if referenced by Offerings."
*   Apply **Outbox Pattern** for events:
    *   `SpecificationCreated`, `SpecificationUpdated`, `SpecificationDeleted`
*   **Verification:**
    *   Create Characteristic → Verify it appears in Spec Service cache (via direct DB check).
    *   Create Spec with cached Char ID → 201 Created.
    *   Create Spec with unknown Char ID → 400 Bad Request.
*   **Status Update (Jan 16, 2026):**
    *   **Specification Service Implemented:** Established the service with full CRUD capabilities and cross-service validation.
    *   **Local Cache Architecture:** Implemented `CachedCharacteristicORM` to maintain autonomy from Characteristic Service.
    *   **Event-Driven Sync:** Integrated `RabbitMQConsumer` to automatically sync the local cache when characteristics are created, updated, or deleted.
    *   **Reliability:** Applied the Transactional Outbox pattern for all specification-related events.
    *   **Verified:** Comprehensive tests (Unit, Integration, Component) passed, including regression testing of the entire system.

### Phase 8: Commercial Domain (Pricing Service)

**Goal:** Handle the money domain with Saga lock support.

*   Implement `Pricing Service` following Clean Architecture.
*   Domain Model fields:
    *   id (UUID), name (unique), value (Decimal, positive, max 2 decimals)
    *   unit (string, e.g., "per month"), currency (enum: USD, EUR, TRY)
    *   locked (boolean), locked_by_saga_id (UUID, nullable)
    *   createdAt, updatedAt
*   Implement endpoints:
    *   CRUD operations
    *   `POST /api/v1/prices/{id}/lock` - Lock for Saga
    *   `POST /api/v1/prices/{id}/unlock` - Unlock (compensating transaction)
*   Validation: Locked prices cannot be deleted or modified → 423 Locked.
*   Apply **Outbox Pattern** for events:
    *   `PriceCreated`, `PriceUpdated`, `PriceDeleted`, `PriceLocked`, `PriceUnlocked`
*   **Verification:** 
    *   Create, update, delete Price.
    *   Lock price → locked=true.
    *   Try to delete locked price → 423 Locked.
    *   Unlock price → locked=false.

**Status Update (Jan 16, 2026):**
*   **Pricing Service Implemented:** Established the service with full CRUD capabilities and Saga locking support.
*   **Domain Logic:** Enforced positive price values and unique name constraints.
*   **Saga Integration:** Implemented `lock` and `unlock` endpoints to support distributed transactions.
*   **Transactional Outbox:** Integrated for all pricing events (`PriceCreated`, `Updated`, `Deleted`, `Locked`, `Unlocked`).
*   **Verified:** Comprehensive tests (Unit, Integration, Component) passed, ensuring reliability and correct behavior under lock.

### Phase 9: The Aggregate Root (Offering Service - Part 1) ✅ Implemented

**Goal:** Manage the complex Lifecycle State Machine.

*   Implement `Offering Service` following Clean Architecture.
*   Domain Model (Aggregate Root):
    *   id, name, description, specificationIds[], pricingIds[], salesChannels[]
    *   lifecycleStatus (enum: DRAFT, PUBLISHING, PUBLISHED, RETIRED)
    *   createdAt, updatedAt, publishedAt, retiredAt
*   Implement **State Machine Logic**:
    ```
    DRAFT → PUBLISHING → PUBLISHED → RETIRED
      ↑         ↓
      └─── (saga fails)
    ```
*   Domain Methods:
    *   `canPublish()`: Returns validation result (needs 1+ spec, 1+ price, 1+ channel).
    *   `publish()`: Validates, transitions to PUBLISHING (will later trigger Camunda).
    *   `confirmPublication()`: Transitions PUBLISHING → PUBLISHED.
    *   `failPublication()`: Transitions PUBLISHING → DRAFT.
    *   `retire()`: Transitions PUBLISHED → RETIRED.
*   Implement validation:
    *   Cross-service: Validate Spec IDs exist (HTTP to Specification Service).
    *   Cross-service: Validate Price IDs exist (HTTP to Pricing Service).
*   Apply **Outbox Pattern** for events:
    *   `OfferingCreated`, `OfferingUpdated`, `OfferingPublicationInitiated`
    *   `OfferingPublished`, `OfferingPublicationFailed`, `OfferingRetired`
*   **Note:** Mock the `publish()` to simply change state for now (no Camunda yet).
*   **Verification:** 
    *   Create Offering (DRAFT).
    *   Update with Specs/Prices/Channels.
    *   Publish without requirements → 400 Bad Request.
    *   Publish with all requirements → State changes to PUBLISHING → PUBLISHED (mocked).
*   **Status Update (Jan 16, 2026):**
    *   **Offering Service Implemented:** Clean Architecture implementation completed.
    *   **Lifecycle State Machine:** Fully functional with transitions (DRAFT -> PUBLISHING -> PUBLISHED/DRAFT, PUBLISHED -> RETIRED).
    *   **Cross-Service Validation:** Implemented synchronous HTTP calls to verify Specification and Pricing IDs.
    *   **Transactional Outbox:** Integrated for all lifecycle events.
    *   **Verified:** Unit tests for domain logic, integration tests for outbox, and component tests for API with external service mocking all passing.

---

## PART III: ADVANCED PATTERNS (CQRS & SAGA)

### Phase 10: The Read Model (Store Service & CQRS) ✅ Implemented

**Goal:** Make data viewable and searchable (Event-Driven Synchronization).

*   Implement `Store Query Service` (Read side of CQRS).
*   Data stores:
    *   **MongoDB:** Denormalized `PublishedOffering` documents.
    *   **Elasticsearch:** Full-text search index with facets.
*   Implement **RabbitMQ Consumers** for ALL events:
    *   `CharacteristicCreated`, `CharacteristicUpdated`, `CharacteristicDeleted`
    *   `SpecificationCreated`, `SpecificationUpdated`, `SpecificationDeleted`
    *   `PriceCreated`, `PriceUpdated`, `PriceDeleted`
    *   `OfferingPublished`, `OfferingRetired`
*   Implement **Idempotency**:
    *   Store processed event IDs in separate MongoDB collection.
    *   Skip processing if event already handled.
*   Event Handler Logic:
    *   On `OfferingPublished`: Fetch full data via HTTP, create denormalized document, index in Elasticsearch.
    *   On `OfferingRetired`: Remove from MongoDB and Elasticsearch.
    *   On `Characteristic/Spec/Price Updated`: Find affected offerings, re-fetch, update documents.
*   Implement Search API:
    *   `GET /api/v1/store/offerings` - List with pagination.
    *   `GET /api/v1/store/offerings/{id}` - Single offering detail.
    *   `GET /api/v1/store/search` - Full-text search with filters.
*   Search Capabilities:
    *   Full-text search across name, description, characteristic values.
    *   Price range filter (min/max).
    *   Characteristic facets (e.g., speed >= 100 Mbps).
    *   Sort by price, name, published date.
*   **Verification:** 
    *   Create Char/Spec/Price/Offering in Write APIs.
    *   Publish Offering.
    *   Wait 1-2 seconds (eventual consistency).
    *   Query Store API → See aggregated, denormalized object.
    *   Search with filters → Correct results returned.
*   **Status Update (Jan 16, 2026):**
    *   **Store Query Service Implemented:** Full CQRS read side with MongoDB and Elasticsearch.
    *   **Event-Driven Synchronization:** All required consumers implemented with idempotency checks.
    *   **Data Composition:** Logic to aggregate data from multiple services via HTTP is functional.
    *   **Verified:** Unit and component tests cover event handling, search query construction, and API endpoints. All tests passed.

### Phase 11: The API Gateway & Resilience

**Goal:** Unify the entry point and protect the system.

*   Implement full `api-gateway` routing to all 6 services:
    *   `/api/v1/auth/*` → Identity Service
    *   `/api/v1/characteristics/*` → Characteristic Service
    *   `/api/v1/specifications/*` → Specification Service
    *   `/api/v1/prices/*` → Pricing Service
    *   `/api/v1/offerings/*` → Offering Service
    *   `/api/v1/store/*` → Store Query Service
*   Implement **Circuit Breakers** (pybreaker) for ALL downstream services:
    *   Failure threshold: 3 consecutive failures
    *   Open circuit duration: 20 seconds
    *   Half-open test requests: 3
*   Implement **Timeouts**:
    *   Connection timeout: 2 seconds
    *   Read timeout: 4 seconds
*   Implement **CORS Handler** for frontend.
*   Implement **Correlation ID** management:
    *   Generate `X-Correlation-ID` if not present.
    *   Forward to all downstream services.
*   Implement **Health Endpoints**:
    *   `GET /health` - Gateway health.
    *   `GET /health/dependencies` - All downstream services status.
*   **Verification:** 
    *   Route requests correctly to all services.
    *   Stop Characteristic container → Gateway returns 503 immediately (circuit open).
    *   Restart container → Circuit closes, requests succeed.
*   **Status Update (Jan 16, 2026):**
    *   **API Gateway Implemented:** Unified routing for all 6 microservices.
    *   **Resilience:** Custom `AsyncCircuitBreaker` and `httpx` timeouts implemented and verified.
    *   **Observability:** Correlation ID tracking and process timing headers added.
    *   **Verification:** Comprehensive component tests passed, covering routing, circuit breakers, and timeouts.

### Phase 12: Distributed Transactions (The Saga)

**Goal:** The "Boss Level" - Orchestrating the Publish flow.

*   Create and deploy **BPMN diagram** to Camunda:
    *   Process name: `offering-publication-saga`
    *   External tasks with topics: `lock-prices`, `validate-specifications`, `create-store-entry`, `confirm-publication`
*   Implement **Python External Task Workers**:
    *   **Pricing Service Worker** (topic: `lock-prices`):
        *   Lock all prices for the offering.
        *   On failure: Fail task, trigger compensation.
    *   **Specification Service Worker** (topic: `validate-specifications`):
        *   Verify all specs still exist and are valid.
        *   On failure: Fail task.
    *   **Store Service Worker** (topic: `create-store-entry`):
        *   Pre-create denormalized document.
        *   On failure: Fail task.
    *   **Offering Service Worker** (topic: `confirm-publication`):
        *   Update lifecycle to PUBLISHED, set publishedAt.
        *   Publish `OfferingPublished` event.
*   Implement **Compensating Transactions** (on saga failure):
    *   Unlock all locked prices.
    *   Delete partial store entry.
    *   Revert offering to DRAFT.
    *   Publish `OfferingPublicationFailed` event.
*   Update `Offering Service` to trigger Camunda process instead of mock state change.
*   **Verification:** 
    *   Click "Publish" via API.
    *   Watch Camunda Cockpit → See tokens move through tasks.
    *   Check Prices are "Locked".
    *   Check Offering state becomes "PUBLISHED".
    *   Force a task failure → Verify compensation runs, offering reverts to DRAFT.
*   **Tests:**
    *   **Integration:** Mock Camunda start call and downstream validations; verify `/publish` transitions to `PUBLISHING` and persists.
    *   **Component:** Verify `/confirm` transitions `PUBLISHING → PUBLISHED`, `/fail` transitions `PUBLISHING → DRAFT`, and update is blocked outside `DRAFT`.
    *   **Regression:** Run full Offering Service test suite to ensure existing CRUD/outbox behavior remains intact.
*   **Status Update (Jan 16, 2026):**
    *   **BPMN Added:** `docs/camunda/offering_publication_saga.bpmn` created for Camunda deployment.
    *   **Saga Entry:** Offering `/publish` now starts Camunda and leaves state as `PUBLISHING` until confirmation.
    *   **Workers Implemented (Code):** Worker handlers added per service (not auto-started inside API process to keep services testable and avoid blocking threads).
    *   **Verified:** Saga-focused integration/component tests added and passing; full Offering Service tests passing.

### Phase 13: Observability & Tracing ✅ Implemented

**Goal:** Prove you know what is happening inside.

*   Enable **OpenTelemetry** in the Shared Chassis:
    *   Auto-instrumentation for FastAPI, HTTP clients, SQLAlchemy.
    *   B3 trace context propagation via HTTP headers.
    *   Trace context propagation via RabbitMQ message headers.
*   Span naming convention:
    *   HTTP: `{method} {path}` (e.g., "POST /offerings")
    *   Database: `{operation} {table}` (e.g., "SELECT offerings")
    *   Messaging: `PUBLISH {topic}` or `CONSUME {queue}`
    *   Saga: `SAGA {process_name} {task_name}`
*   Configure **ELK Stack**:
    *   Services write JSON logs to stdout.
    *   Filebeat ships logs to Logstash.
    *   Logstash parses and forwards to Elasticsearch.
    *   Kibana dashboards for log search by correlation ID.
*   **Verification:** 
    *   Make a request that spans multiple services (e.g., publish offering).
    *   Open Zipkin UI → See waterfall chart spanning HTTP and async boundaries.
    *   Open Kibana → Search by correlation ID → See all related logs.

*   **Status Update (Jan 16, 2026):**
    *   **Tracing Module:** `libs/common-python/src/common/tracing.py` created with OpenTelemetry setup, B3 propagation, and auto-instrumentation helpers.
    *   **Logging Enhanced:** `logging.py` updated to auto-inject `trace_id` and `span_id` from OTel context into JSON logs.
    *   **Messaging Traced:** `messaging.py` updated to propagate B3 headers in RabbitMQ message headers (PRODUCER/CONSUMER spans).
    *   **All Services Instrumented:** API Gateway and all 6 microservices now initialize tracing and instrument FastAPI.
    *   **ELK Configured:** `logstash.conf` updated to parse trace fields; Elasticsearch template added for optimal field mappings.
    *   **Docker-Compose Updated:** Logstash port 5044 exposed; healthcheck added.
    *   **Tests Added:** Unit tests for tracing utilities; integration tests for B3 header propagation.

---

## PART IV: FRONTEND (NextJS)

### ### Phase 14: UI Scaffold & Authentication ✅

**Status:** Implemented (Modern Next.js 14, Orange Branding, JWT Auth)

**Goal:** A working web app that can log in.

*   ✅ Initialize NextJS 14+ with App Router + Tailwind CSS.
*   ✅ Implement the **Auth Context**:
    *   ✅ Login page (`/login`) with username/password form.
    *   ✅ Store JWT in localStorage.
    *   ✅ AuthProvider wraps app, provides user state.
    *   ✅ Intercept 401 responses → Redirect to login.
    *   ✅ Token expiration handling.
*   ✅ Create the **Navigation Layout**:
    *   ✅ Header with logo, nav links, user indicator, logout button.
    *   ✅ Main navigation: Builder, Viewer, Store.
    *   ✅ Protected routes redirect to `/login` if not authenticated.
*   ✅ Set up **API Client**:
    *   ✅ Base URL from environment variable.
    *   ✅ Auto-attach Authorization header.
    *   ✅ Error handling wrapper.

---

### Phase 15: The Builder (Admin UI - Create Entities)

**Goal:** Enable data entry for all entity types.

*   Implement **Builder Page** with 4 tabs:
    *   **Tab 1: Create Characteristic**
        *   Form: Name, Value, Unit of Measure (dropdown).
        *   Submit → POST /api/v1/characteristics.
        *   Success toast, clear form.
    *   **Tab 2: Create Specification**
        *   Form: Name, Characteristics (multi-select with search).
        *   Fetch characteristics on mount for dropdown.
        *   Display selected as chips/tags.
        *   Submit → POST /api/v1/specifications.
    *   **Tab 3: Create Pricing**
        *   Form: Name, Value (decimal), Unit, Currency (dropdown).
        *   Submit → POST /api/v1/prices.
    *   **Tab 4: Create Product Offering**
        *   Form: Name, Description, Specifications (multi-select), Prices (multi-select), Sales Channels (checkboxes).
        *   Lifecycle Status display (starts as DRAFT).
        *   "Save Draft" button → POST /api/v1/offerings.
        *   "Publish" button (enabled when valid) → POST /api/v1/offerings/{id}/publish.
*   Implement **Form Validation**:
    *   Client-side required field validation.
    *   Server-side error display.
*   Implement **Loading States**:
    *   Spinners on submit buttons.
    *   Disable buttons during async operations.
*   **Verification:** Create a full product hierarchy using ONLY the UI.

### Phase 16: The Viewer (Admin UI - Manage Entities)

**Goal:** View, edit, and delete existing entities.

*   Implement **Viewer Page** with 4 tabs:
    *   **Tab 1: View Characteristics**
        *   Table: Name, Value, Unit, Created Date.
        *   Pagination (20 per page).
        *   Search/filter by name.
        *   Edit button → Modal with pre-filled form → PUT /api/v1/characteristics/{id}.
        *   Delete button → Confirmation dialog → DELETE /api/v1/characteristics/{id}.
        *   Handle "Cannot delete, used by specifications" error.
    *   **Tab 2: View Specifications**
        *   Table: Name, Characteristics (comma-separated), Created Date.
        *   Click to expand characteristic details.
        *   Edit and Delete with dependency error handling.
    *   **Tab 3: View Prices**
        *   Table: Name, Value, Unit, Currency, Status (Locked/Unlocked).
        *   Lock icon with tooltip for locked prices.
        *   Edit/Delete with lock error handling (423 Locked).
    *   **Tab 4: View Offerings**
        *   Table: Name, Lifecycle Status (badge), Published Date.
        *   Filter by lifecycle status (All, Draft, Published, Retired).
        *   Actions based on status:
            *   DRAFT: Edit, Publish, Delete
            *   PUBLISHED: Retire, View Details
            *   RETIRED: View Details only
        *   Detail modal showing full hierarchy.
*   **Verification:** 
    *   View all entity types.
    *   Edit an entity → Changes reflected.
    *   Delete with dependency → Error displayed.
    *   Filter offerings by status.

### Phase 17: The Store & Saga Polling (Public UI)

**Goal:** The Customer experience and Saga feedback.

*   Implement **Store Page** (public, no auth required):
    *   **Search Bar:** Full-text search with debounce (300ms).
    *   **Filters Panel** (sidebar):
        *   Price range slider (min/max).
        *   Characteristic filters (dynamic based on available characteristics).
        *   Sales channel checkboxes.
        *   Clear filters button.
    *   **Results Grid:** 
        *   Card layout (3-4 columns desktop, 1-2 mobile).
        *   Each card: Name, Price, Key characteristics, "View Details" button.
    *   **Detail View:** Modal or page with full offering info.
    *   **Pagination:** Load more or infinite scroll.
    *   **URL State:** Filters reflected in URL query params (bookmarkable).
*   Implement **Saga Feedback** (in Builder/Viewer):
    *   When user clicks "Publish":
        *   Show loading spinner.
        *   Poll `GET /api/v1/offerings/{id}` every 2 seconds.
        *   Max 30 attempts (1 minute timeout).
        *   On PUBLISHED → Success toast.
        *   On DRAFT (failed) → Error toast with failure reason.
        *   On timeout → Warning toast.
*   **Verification:** 
    *   Full "Happy Path": Create → Publish → Watch Spinner → See in Store.
    *   Search and filter in Store → Correct results.
    *   Force saga failure → Offering reverts, error displayed.

---

## PART V: TESTING & DOCUMENTATION

### Phase 18: Comprehensive Testing

**Goal:** Ensure system reliability with proper test coverage.

*   **Unit Tests** (pytest):
    *   Domain logic for all services (80% coverage target).
    *   Business rules, invariants, state transitions.
    *   Mock external dependencies.
*   **Integration Tests**:
    *   Repository tests with real PostgreSQL (testcontainers).
    *   Message publishing tests with real RabbitMQ.
    *   HTTP client tests with mocked services.
*   **Component Tests**:
    *   Full service tests with real database, mocked external services.
    *   Test complete request/response cycles.
*   **E2E Tests** (optional, Playwright):
    *   Login flow.
    *   Create characteristic → specification → price → offering.
    *   Publish offering.
    *   View in store.
*   **Verification:** 
    *   `pytest --cov` shows 80%+ coverage on domain code.
    *   All tests pass in CI pipeline.

### Phase 19: Documentation & Report

**Goal:** Complete project documentation for submission.

*   **Update SDD** with final architecture diagrams.
*   **Generate API Documentation** (FastAPI auto-docs + export to markdown).
*   **Write Final Report**:
    *   Problem definition (TMF catalog requirements).
    *   User stories and scenarios.
    *   Non-functional requirements.
    *   Architecture diagrams (context, container, component).
    *   Service decomposition rationale (bounded contexts).
    *   Design patterns applied (CQRS, Saga, Outbox, Circuit Breaker).
    *   Technology stack justification.
    *   Database schemas.
    *   Testing strategy and results.
    *   Deployment instructions.
    *   Evaluation and future improvements.
*   **Create README** with:
    *   Project overview.
    *   Prerequisites.
    *   Setup instructions (`docker-compose up`).
    *   `.env.example` file.
    *   Demo walkthrough steps.
*   **Verification:** All documentation complete and accurate.

### Phase 20: Demo Video Production

**Goal:** Create the 5-minute demo video for submission.

*   **Script & Record** (max 5 minutes):
    1.  **Architecture Overview** (30s): Show system diagram.
    2.  **Live Demo Walkthrough**:
        *   Login (10s).
        *   Create Characteristic (20s).
        *   Create Specification with dependency (20s).
        *   Create Pricing (20s).
        *   Create and Publish Offering - show saga spinner (60s).
        *   View in Store page (30s).
        *   Search and filter demo (20s).
    3.  **Technical Highlights**:
        *   Open Camunda Cockpit - show process instance (30s).
        *   Open Zipkin - show distributed trace (30s).
        *   Open Kibana - show logs with correlation ID (20s).
    4.  **Conclusion** (20s).
*   **Verification:** Video is under 5 minutes, covers all key features, audio is clear.

---

## Summary Checklist

### Code Deliverables
- [ ] Monorepo with all 6 services + Gateway + Frontend
- [ ] Docker Compose file (working, documented)
- [ ] Database migrations (Alembic scripts)
- [ ] Shared chassis library (libs/common-python)
- [ ] Camunda BPMN files
- [ ] Frontend application
- [ ] README with setup instructions
- [ ] .env.example file

### Documentation
- [ ] System Design Document (SDD)
- [ ] API Specifications
- [ ] Final Report

### Demo
- [ ] 5-minute video walkthrough

