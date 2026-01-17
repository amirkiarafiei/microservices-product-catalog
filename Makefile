# Monorepo Management Makefile

.PHONY: help infra-up infra-down setup-keys migrate backend frontend dev stop status

help:
	@echo "TMF Product Catalog Microservices - Management"
	@echo "-----------------------------------------------"
	@echo "Infrastructure Commands:"
	@echo "  make infra-up      - Start Docker infrastructure (Postgres, RabbitMQ, etc.)"
	@echo "  make infra-down    - Stop Docker infrastructure"
	@echo ""
	@echo "First-Time Setup (Run once):"
	@echo "  make setup-keys    - Generate RSA keys for JWT"
	@echo "  make migrate       - Run database migrations for all services"
	@echo ""
	@echo "Development Commands:"
	@echo "  make backend       - Start all 7 backend services in background"
	@echo "  make frontend      - Start the Next.js frontend"
	@echo "  make dev           - Start everything (Backend + Frontend)"
	@echo "  make stop          - Stop all running backend services"
	@echo "  make status        - Check which services are running on ports"
	@echo "  make clean-logs    - Delete all backend log files"

# --- Infrastructure ---
infra-up:
	docker compose up -d

infra-down:
	docker compose down

# --- Setup ---
setup-keys:
	./scripts/generate_keys.sh

migrate:
	python scripts/migrate.py upgrade head

# --- Development ---

backend:
	@echo "Starting backend services..."
	@cd services/api-gateway && uv run uvicorn gateway.main:app --port 8000 > ../../logs-gateway.log 2>&1 &
	@cd services/identity-service && uv run uvicorn src.main:app --port 8001 > ../../logs-identity.log 2>&1 &
	@cd services/characteristic-service && uv run uvicorn src.main:app --port 8002 > ../../logs-characteristic.log 2>&1 &
	@cd services/specification-service && uv run uvicorn src.main:app --port 8003 > ../../logs-specification.log 2>&1 &
	@cd services/pricing-service && uv run uvicorn pricing.main:app --port 8004 > ../../logs-pricing.log 2>&1 &
	@cd services/offering-service && uv run uvicorn offering.main:app --port 8005 > ../../logs-offering.log 2>&1 &
	@cd services/store-service && uv run uvicorn store.main:app --port 8006 > ../../logs-store.log 2>&1 &
	@echo "Backend services are starting. Check logs-*.log for output."

frontend:
	cd web-ui && npm run dev

dev: backend frontend

clean-logs:
	rm -f logs-*.log

stop:
	@echo "Stopping backend services..."
	@pkill -f "uvicorn" || true
	@echo "Backend services stopped."

status:
	@echo "Service Status (Port check):"
	@lsof -i :8000 -sTCP:LISTEN && echo "  [UP] Gateway (8000)" || echo "  [DOWN] Gateway (8000)"
	@lsof -i :8001 -sTCP:LISTEN && echo "  [UP] Identity (8001)" || echo "  [DOWN] Identity (8001)"
	@lsof -i :8002 -sTCP:LISTEN && echo "  [UP] Characteristic (8002)" || echo "  [DOWN] Characteristic (8002)"
	@lsof -i :8003 -sTCP:LISTEN && echo "  [UP] Specification (8003)" || echo "  [DOWN] Specification (8003)"
	@lsof -i :8004 -sTCP:LISTEN && echo "  [UP] Pricing (8004)" || echo "  [DOWN] Pricing (8004)"
	@lsof -i :8005 -sTCP:LISTEN && echo "  [UP] Offering (8005)" || echo "  [DOWN] Offering (8005)"
	@lsof -i :8006 -sTCP:LISTEN && echo "  [UP] Store (8006)" || echo "  [DOWN] Store (8006)"
