# Potential Design Smells and Architectural Risks

This document outlines potential issues identified during the design review of the TMF Product Catalog Microservices. These points are not definitive bugs but rather architectural considerations that might lead to failures, technical debt, or performance bottlenecks if not addressed during the implementation phases.

## 1. Temporal Coupling via Synchronous Validation
### Potential Issue
In the current design, the **Specification Service** is planned to make synchronous HTTP calls to the **Characteristic Service** to validate IDs during the creation of a specification. This creates a temporal coupling where the availability of the Specification Service becomes dependent on the uptime of the Characteristic Service.

### Possible Solutions
- **Local Reference Cache**: The Specification Service could maintain a local, read-only table of valid Characteristic IDs, synchronized via domain events from the Characteristic Service.
- **Asynchronous Validation**: Accept the request, return a `202 Accepted` status, and validate the specification asynchronously, marking it as `INVALID` or `ERROR` if the characteristics do not exist.

## 2. Event vs. Saga Race Conditions
### Potential Issue
The **Store Query Service** (the read model) receives updates from two sources: direct RabbitMQ domain events (e.g., `OfferingUpdated`) and Camunda Saga tasks (e.g., "Index in Store"). There is a possibility that a newer domain event could be processed before an older Saga task completes, or vice versa, leading to an inconsistent state in the MongoDB/Elasticsearch read models.

### Possible Solutions
- **Optimistic Concurrency/Versioning**: Include a version number or a high-resolution timestamp in every event and document. The consumer should ignore any updates that have a version lower than or equal to the currently stored version.
- **Single Source of Truth for Reads**: Route all read-model updates through the same event-driven pipeline to ensure sequential processing for a specific aggregate ID.

## 3. At-Least-Once Delivery & Idempotency
### Potential Issue
The **Transactional Outbox** pattern (using `LISTEN/NOTIFY`) guarantees at-least-once delivery. If the outbox worker crashes after publishing an event to RabbitMQ but before marking it as `SENT` in the database, the event will be duplicated upon worker restart.

### Possible Solutions
- **Consumer Idempotency**: Ensure all event consumers (like the Store Query Service) track processed `event_id`s in an idempotency table or use unique constraints in the database to prevent duplicate processing.

## 4. Saga Completion & State Consistency
### Potential Issue
During the publication saga, multiple services (Price, Store, Offering) are involved. If the Saga orchestrator (Camunda) successfully completes all external tasks but the final state update to the **Offering Service** fails (e.g., due to a network timeout), the offering might remain in a `PUBLISHING` state indefinitely while the Price is locked and the Store is updated.

### Possible Solutions
- **Idempotent Completion Step**: The final step of the Camunda BPMN should be a retryable, idempotent call to the Offering Service to transition it to the `PUBLISHED` state.
- **Reconciliation Job**: Implement a background "sweeper" in the Offering Service to identify offerings stuck in `PUBLISHING` for too long and query the Saga state to resolve them.

## 5. Performance Bottlenecks in Search Re-indexing
### Potential Issue
The design suggests that when a "Price" or "Specification" is updated, the system should find all affected "Offerings" and re-index them in the Store Query Service. If a single specification is shared by thousands of offerings, a single update could trigger a massive wave of HTTP "re-fetch" requests or database lookups.

### Possible Solutions
- **Denormalized Relationship Mapping**: Store the relationship tree within the read database (MongoDB) to allow for bulk updates without re-fetching the entire aggregate from the write-side microservices.
- **Bulk Event Processing**: Implement a buffer or windowing mechanism to batch re-indexing requests for the same parent entity.

## 6. Infrastructure Complexity vs. Requirements
### Potential Issue
Using **Camunda 7** (a full BPMN engine) for a linear 4-step saga might introduce significant operational overhead and infrastructure complexity for the current project scope.

### Possible Solutions
- **Choreography-based Saga**: Evaluate if a simpler event-driven choreography (where services listen for events and trigger the next step) would suffice for the initial version.
- **Lightweight Orchestrator**: Consider a code-based state machine if the visual BPMN modeling is not strictly required for business stakeholders.

## 7. Security: Token Revocation
### Potential Issue
The design relies on JWT (RS256) validation. Standard JWTs are stateless, meaning once a token is issued, it cannot be easily revoked until it expires.

### Possible Solutions
- **Refresh Token Pattern**: Issue short-lived Access Tokens and longer-lived Refresh Tokens, allowing the **Identity Service** to "revoke" access by invalidating the refresh token.
- **Token Blacklisting**: Implement a distributed cache (like Redis) at the API Gateway to store revoked token signatures.
