Here is your **Incremental Roadmap**.

---

## PART I: BACKEND INFRASTRUCTURE & CORE (The Foundation)

### Phase 1: The Monorepo Skeleton & Infrastructure
**Goal:** Establish the physical environment where code lives and runs.
*   Initialize the `uv` monorepo workspace and Git repository.
*   Create the master `docker-compose.yml` defining all infrastructure (Postgres, RabbitMQ, Mongo, Camunda, Zipkin, Keycloak/Auth).
*   Create a "Hello World" service (`api-gateway`) just to prove that Python can talk to Docker and ports are exposed correctly.
*   **Verification:** `docker-compose up` runs without exiting. You can curl the Gateway and get a 200 OK.

### Phase 2: The Shared Chassis (Library)
**Goal:** Define *how* code is written so we don't repeat ourselves.
*   Create `libs/common-python`.
*   Implement standard **Structured Logging** (JSON format).
*   Implement **Configuration Management** (Pydantic settings reading from Envs).
*   Implement the **Standard Exception Hierarchy** (Not Found, Validation Error, Domain Error).
*   **Verification:** Write a unit test in the library that logs a JSON message and handles a custom exception.

### Phase 3: Identity & Security (Zero Trust)
**Goal:** secure the system before building business logic.
*   Implement the **Identity Service** (or configure Keycloak).
*   Define the **JWT Schema** (User ID, Roles).
*   Update the `common-python` Chassis with a `verify_jwt` dependency.
*   **Verification:** Generate a token via `POST /login`. Use that token to hit a protected endpoint in the "Hello World" gateway. Fail without token. Pass with token.

---

## PART II: DOMAIN IMPLEMENTATION (Clean Architecture)

### Phase 4: The First Vertical Slice (Characteristic Service)
**Goal:** Establish the pattern for **Clean Architecture** (Domain -> Application -> Infra).
*   Implement `Characteristic Service` (Write side).
*   Define Domain Entities (`Characteristic`) and Pydantic DTOs.
*   Implement Repository layer with SQLAlchemy (Postgres).
*   **Crucial:** Do **NOT** implement Outbox or RabbitMQ yet. Just pure CRUD.
*   **Verification:** `pytest` passes for Domain logic. `curl` to create and read a Characteristic from Postgres.

### Phase 5: The Event Engine (Transactional Outbox)
**Goal:** Enable reliable async messaging without breaking the DB transaction.
*   Extend `common-python` with the **Outbox Table Model**.
*   Implement the **Postgres LISTEN/NOTIFY** listener (background thread).
*   Implement the **RabbitMQ Publisher** wrapper.
*   Update `Characteristic Service` to write to Outbox on create/update.
*   **Verification:** Create a Characteristic via API. Check Postgres `outbox` table (status: SENT). Check RabbitMQ Management UI to see the message in the queue.

### Phase 6: Dependency Management (Specification Service)
**Goal:** Handle cross-service synchronous dependencies.
*   Implement `Specification Service` (Write side).
*   Implement the "Synchronous Validator" (HTTP Client) that calls Characteristic Service to check if IDs exist.
*   Implement Domain Logic: "A spec must have at least 1 characteristic."
*   **Verification:** Try to create a Spec with a fake Char ID (should fail 400). Create with real ID (should pass 201).

### Phase 7: Commercial Domain (Pricing Service)
**Goal:** Handle the money domain.
*   Implement `Pricing Service`.
*   Add the `locked` boolean field to the database schema (preparation for Saga).
*   Implement basic CRUD.
*   **Verification:** Create a Price. Update it. Delete it. Standard Component tests.

### Phase 8: The Aggregate Root (Offering Service - Part 1)
**Goal:** Manage the complex Lifecycle State Machine (Draft/Published).
*   Implement `Offering Service`.
*   Implement the State Machine Logic (DRAFT -> PUBLISHING -> PUBLISHED).
*   Implement validation: "Cannot publish without Spec ID and Price ID."
*   **Note:** Do not implement Camunda yet. Just mock the `publish()` method to simply change the state for now.
*   **Verification:** Create an Offering (Draft). Add Specs/Prices. Try to "Publish" (State changes).

---

## PART III: ADVANCED PATTERNS (CQRS & SAGA)

### Phase 9: The Read Model (Store Service & CQRS)
**Goal:** Make data viewable and searchable (Syncing Data).
*   Implement `Store Query Service`.
*   Implement **RabbitMQ Consumers** for `CharacteristicCreated`, `SpecCreated`, `PriceCreated`, `OfferingPublished`.
*   Implement the Logic: When an event arrives, update the **MongoDB/Elastic** document.
*   **Verification:** Create a Char/Spec/Price/Offering in the Write APIs. Wait 1 second. Query the Store API to see the aggregated object.

### Phase 10: The API Gateway & Resilience
**Goal:** Unify the entry point and protect the system.
*   Update `api-gateway` to route to all 5 real services.
*   Implement **Circuit Breakers** (pybreaker) for the Specification -> Characteristic synchronous call.
*   **Verification:** Stop the Characteristic container. Call the Gateway. It should return a "Service Unavailable" JSON immediately, not hang.

### Phase 11: Distributed Transactions (The Saga)
**Goal:** The "Boss Level" - Orchestrating the Publish flow.
*   Deploy the BPMN diagram to **Camunda**.
*   Implement **Python Workers** in Pricing (Lock), Spec (Validate), and Store (Create Entry).
*   Update `Offering Service` to trigger the Camunda process instead of changing state directly.
*   **Verification:** Click "Publish". Watch Camunda Cockpit. See tokens move. Check Price is "Locked". Check State becomes "PUBLISHED".

### Phase 12: Observability & Tracing
**Goal:** Prove you know what is happening inside.
*   Enable **OpenTelemetry** in the Chassis.
*   Ensure `Trace-ID` is passed from Gateway -> Service -> RabbitMQ -> Consumer.
*   **Verification:** specific request in Zipkin UI. See the waterfall chart spanning HTTP and Async boundaries.

---

## PART IV: FRONTEND (NextJS)

### Phase 13: UI Scaffold & Authentication
**Goal:** A working web app that can log in.
*   Initialize NextJS + Tailwind.
*   Implement the **Auth Context** (Login page, store JWT, intercept 401s).
*   Create the Navigation Layout (Builder / Viewer / Store).
*   **Verification:** Login redirects to Dashboard. Logout redirects to Login.

### Phase 14: The Builder & Viewer (Admin UI)
**Goal:** Enable data entry and management.
*   Implement "Builder" forms for all 4 entities (using multi-selects for dependencies).
*   Implement "Viewer" grids (Read-only tables).
*   Connect them to the API Gateway.
*   **Verification:** Create a full product hierarchy using ONLY the UI.

### Phase 15: The Store & Polling (Public UI)
**Goal:** The Customer experience and Saga feedback.
*   Implement the Store Grid (Search & Filter).
*   Implement **Saga Feedback**: When user clicks "Publish", show a spinner and poll the status endpoint until it flips to "PUBLISHED".
*   **Verification:** The full "Happy Path" demo. Create -> Publish -> Watch Spinner -> See in Store.

