# CLAUDE.md - Development Guide

## Build and Run Commands

### Infrastructure
- **Start all services**: `docker-compose up -d`
- **Stop all services**: `docker-compose down`
- **View logs**: `docker-compose logs -f`

### Backend (Python/FastAPI)
- **Install dependencies**: `uv sync` (from root or service directory)
- **Run a service**: `uv run uvicorn app.main:app --reload --port <port>`
- **Database Migrations**: `alembic upgrade head` (per service)
- **Create Migration**: `alembic revision --autogenerate -m "description"`

### Frontend (Next.js)
- **Install dependencies**: `npm install`
- **Run development server**: `npm run dev`
- **Build for production**: `npm run build`

## Test Commands
- **Run all Python tests**: `pytest`
- **Run specific Python test**: `pytest path/to/test.py`
- **Run Python tests with coverage**: `pytest --cov`
- **Run Frontend tests**: `npm test`

## Code Style Guidelines

### General Principles
- **Clean Architecture**: Follow the Domain -> Application -> Infrastructure dependency flow.
- **DRY & KISS**: Prefer simple, maintainable solutions over complex ones.
- **Structured Logging**: Use JSON formatting with `correlation_id` and `trace_id`.
- **Error Handling**: Use the project's standard exception hierarchy (`ValidationError`, `NotFoundError`, etc.).

### Python (Google Style Guide)
- **Naming**: `snake_case` for variables/functions/modules, `PascalCase` for classes, `ALL_CAPS` for constants.
- **Formatting**: 4 spaces indentation, 80 characters max line length.
- **Typing**: Use type annotations for all public functions and class members.
- **Imports**: Group imports (standard library, third-party, local). Use `import x` or `from x import y` (where y is a submodule).

### TypeScript/React (Google Style Guide)
- **Naming**: `lowerCamelCase` for variables/functions, `UpperCamelCase` for components/interfaces/types.
- **Formatting**: Use `gts` standards: single quotes (`'`), explicit semicolons, 2-space indentation.
- **Typing**: Avoid `any`; prefer specific types or `unknown`.
- **Exports**: Use named exports. Avoid default exports.
- **Components**: Prefer functional components with hooks.

## Architecture Patterns
- **CQRS**: Separate Write (Postgres) and Read (Mongo/Elastic) models.
- **Transactional Outbox**: Use `outbox` table and `LISTEN/NOTIFY` for reliable event publishing.
- **Saga**: Orchestrate multi-service flows via Camunda BPMN.
- **Zero Trust**: Validate JWT (RS256) at both Gateway and Service levels.
