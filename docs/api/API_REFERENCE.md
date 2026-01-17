# API Reference
## TMF Product Catalog Microservices

**Base URL:** `http://localhost:8000` (API Gateway)

**Authentication:** Bearer Token (JWT)  
**Content-Type:** `application/json`

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Characteristics](#2-characteristics)
3. [Specifications](#3-specifications)
4. [Pricing](#4-pricing)
5. [Offerings](#5-offerings)
6. [Store](#6-store)
7. [Health Checks](#7-health-checks)
8. [Error Responses](#8-error-responses)

---

## 1. Authentication

### POST /api/v1/auth/login

Login with username and password to receive a JWT token.

**Request:**
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Response (401 Unauthorized):**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid credentials"
  }
}
```

### GET /api/v1/auth/public-key

Retrieve the public key for JWT verification.

**Response (200 OK):**
```json
{
  "public_key": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
}
```

---

## 2. Characteristics

### GET /api/v1/characteristics

List all characteristics.

**Headers:**
- `Authorization: Bearer <token>` (USER or ADMIN role)

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Number of items to skip |
| `limit` | integer | 100 | Maximum items to return |

**Response (200 OK):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Internet Speed",
    "value": "100",
    "unit_of_measure": "MBPS",
    "created_at": "2026-01-18T00:00:00Z",
    "updated_at": "2026-01-18T00:00:00Z"
  }
]
```

### POST /api/v1/characteristics

Create a new characteristic.

**Headers:**
- `Authorization: Bearer <token>` (ADMIN role required)

**Request Body:**
```json
{
  "name": "Internet Speed",
  "value": "100",
  "unit_of_measure": "MBPS"
}
```

**Valid Units:** `MBPS`, `GBPS`, `GB`, `TB`, `GHZ`, `VOLT`, `WATT`, `METER`, `NONE`, `PERCENT`, `SECONDS`, `MINUTES`, `HOURS`, `DAYS`, `MONTHS`, `YEARS`, `UNIT`

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Internet Speed",
  "value": "100",
  "unit_of_measure": "MBPS",
  "created_at": "2026-01-18T00:00:00Z",
  "updated_at": "2026-01-18T00:00:00Z"
}
```

### GET /api/v1/characteristics/{id}

Get a characteristic by ID.

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Internet Speed",
  "value": "100",
  "unit_of_measure": "MBPS",
  "created_at": "2026-01-18T00:00:00Z",
  "updated_at": "2026-01-18T00:00:00Z"
}
```

### PUT /api/v1/characteristics/{id}

Update an existing characteristic.

**Headers:**
- `Authorization: Bearer <token>` (ADMIN role required)

**Request Body:**
```json
{
  "name": "Internet Speed",
  "value": "200",
  "unit_of_measure": "MBPS"
}
```

### DELETE /api/v1/characteristics/{id}

Delete a characteristic.

**Headers:**
- `Authorization: Bearer <token>` (ADMIN role required)

**Response (204 No Content)**

**Error (409 Conflict):** Cannot delete if referenced by specifications.

---

## 3. Specifications

### GET /api/v1/specifications

List all specifications.

**Headers:**
- `Authorization: Bearer <token>` (USER or ADMIN role)

**Response (200 OK):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Fiber Optic Spec",
    "characteristic_ids": [
      "550e8400-e29b-41d4-a716-446655440000"
    ],
    "created_at": "2026-01-18T00:00:00Z",
    "updated_at": "2026-01-18T00:00:00Z"
  }
]
```

### POST /api/v1/specifications

Create a new specification.

**Headers:**
- `Authorization: Bearer <token>` (ADMIN role required)

**Request Body:**
```json
{
  "name": "Fiber Optic Spec",
  "characteristic_ids": [
    "550e8400-e29b-41d4-a716-446655440000"
  ]
}
```

**Validation:**
- At least 1 characteristic ID required
- All characteristic IDs must exist

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Fiber Optic Spec",
  "characteristic_ids": [
    "550e8400-e29b-41d4-a716-446655440000"
  ],
  "created_at": "2026-01-18T00:00:00Z",
  "updated_at": "2026-01-18T00:00:00Z"
}
```

### GET /api/v1/specifications/{id}

Get a specification by ID with expanded characteristics.

### PUT /api/v1/specifications/{id}

Update an existing specification.

### DELETE /api/v1/specifications/{id}

Delete a specification.

**Error (409 Conflict):** Cannot delete if referenced by offerings.

---

## 4. Pricing

### GET /api/v1/prices

List all prices.

**Response (200 OK):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "name": "Monthly Fee",
    "value": 50.00,
    "unit": "per month",
    "currency": "USD",
    "locked": false,
    "locked_by_saga_id": null,
    "created_at": "2026-01-18T00:00:00Z",
    "updated_at": "2026-01-18T00:00:00Z"
  }
]
```

### POST /api/v1/prices

Create a new price.

**Request Body:**
```json
{
  "name": "Monthly Fee",
  "value": 50.00,
  "unit": "per month",
  "currency": "USD"
}
```

**Valid Currencies:** `USD`, `EUR`, `TRY`

### GET /api/v1/prices/{id}

Get a price by ID.

### PUT /api/v1/prices/{id}

Update an existing price.

**Error (423 Locked):** Cannot modify a locked price.

### DELETE /api/v1/prices/{id}

Delete a price.

**Error (423 Locked):** Cannot delete a locked price.

### POST /api/v1/prices/{id}/lock

Lock a price (used by Saga workflow).

**Request Body:**
```json
{
  "saga_id": "550e8400-e29b-41d4-a716-446655440003"
}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "locked": true,
  "locked_by_saga_id": "550e8400-e29b-41d4-a716-446655440003"
}
```

### POST /api/v1/prices/{id}/unlock

Unlock a price (compensation transaction).

---

## 5. Offerings

### GET /api/v1/offerings

List all offerings.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by lifecycle status |

**Response (200 OK):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "name": "Premium Internet",
    "description": "High-speed fiber optic internet",
    "specification_ids": ["550e8400-e29b-41d4-a716-446655440001"],
    "pricing_ids": ["550e8400-e29b-41d4-a716-446655440002"],
    "sales_channels": ["online", "retail"],
    "lifecycle_status": "DRAFT",
    "created_at": "2026-01-18T00:00:00Z",
    "updated_at": "2026-01-18T00:00:00Z",
    "published_at": null,
    "retired_at": null
  }
]
```

### POST /api/v1/offerings

Create a new offering (starts in DRAFT status).

**Request Body:**
```json
{
  "name": "Premium Internet",
  "description": "High-speed fiber optic internet",
  "specification_ids": ["550e8400-e29b-41d4-a716-446655440001"],
  "pricing_ids": ["550e8400-e29b-41d4-a716-446655440002"],
  "sales_channels": ["online", "retail"]
}
```

**Validation:**
- At least 1 specification ID
- At least 1 pricing ID
- At least 1 sales channel

### GET /api/v1/offerings/{id}

Get an offering by ID.

### PUT /api/v1/offerings/{id}

Update an offering.

**Error (400 Bad Request):** Can only update offerings in DRAFT status.

### DELETE /api/v1/offerings/{id}

Delete an offering.

**Error (400 Bad Request):** Can only delete offerings in DRAFT status.

### POST /api/v1/offerings/{id}/publish

Publish an offering (triggers Saga workflow).

**Preconditions:**
- Offering must be in DRAFT status
- Must have at least 1 spec, 1 price, 1 sales channel

**Response (202 Accepted):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "lifecycle_status": "PUBLISHING",
  "message": "Publication saga started"
}
```

**Saga Steps:**
1. Lock all referenced prices
2. Validate all specifications exist
3. Create store entry (MongoDB + Elasticsearch)
4. Confirm publication

**On Success:** Status → `PUBLISHED`  
**On Failure:** Compensation runs, status → `DRAFT`

### POST /api/v1/offerings/{id}/retire

Retire a published offering.

**Precondition:** Offering must be in PUBLISHED status.

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "lifecycle_status": "RETIRED",
  "retired_at": "2026-01-18T00:00:00Z"
}
```

---

## 6. Store

**Note:** Store endpoints are PUBLIC (no authentication required).

### GET /api/v1/store/offerings

Search published offerings.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Full-text search |
| `min_price` | number | Minimum price filter |
| `max_price` | number | Maximum price filter |
| `skip` | integer | Pagination offset |
| `limit` | integer | Maximum results |

**Example:**
```http
GET /api/v1/store/offerings?query=internet&min_price=20&max_price=100
```

**Response (200 OK):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "name": "Premium Internet",
    "description": "High-speed fiber optic internet",
    "specifications": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "Fiber Optic Spec",
        "characteristics": [
          {
            "name": "Internet Speed",
            "value": "100",
            "unit": "MBPS"
          }
        ]
      }
    ],
    "pricing": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "name": "Monthly Fee",
        "value": 50.00,
        "currency": "USD"
      }
    ],
    "sales_channels": ["online", "retail"],
    "published_at": "2026-01-18T00:00:00Z"
  }
]
```

### GET /api/v1/store/offerings/{id}

Get a published offering by ID with full details.

---

## 7. Health Checks

### GET /health

Basic health check.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "api-gateway"
}
```

### GET /health/dependencies

Check all downstream service dependencies.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "dependencies": {
    "identity": "healthy",
    "characteristic": "healthy",
    "specification": "healthy",
    "pricing": "healthy",
    "offering": "healthy",
    "store": "healthy"
  }
}
```

---

## 8. Error Responses

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {},
    "correlation_id": "uuid"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate name) |
| `LOCKED` | 423 | Resource is locked |
| `SERVICE_UNAVAILABLE` | 503 | Downstream service unavailable |

---

## Interactive Documentation

Each service provides interactive Swagger documentation:

| Service | Swagger UI |
|---------|------------|
| API Gateway | http://localhost:8000/docs |
| Identity | http://localhost:8001/docs |
| Characteristic | http://localhost:8002/docs |
| Specification | http://localhost:8003/docs |
| Pricing | http://localhost:8004/docs |
| Offering | http://localhost:8005/docs |
| Store | http://localhost:8006/docs |

---

*Generated from FastAPI OpenAPI specifications*  
*January 2026*
