 .PHONY: help build start stop restart logs clean test lint format migrate makemigrations install dev setup

# Default target
help:
	@echo "SpendTrack - AI-Powered Personal Finance Manager"
	@echo ""
	@echo "Available commands:"
	@echo "  make build          - Build all Docker containers"
	@echo "  make start          - Start all services"
	@echo "  make stop           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs from all services"
	@echo "  make logs-backend   - View backend logs"
	@echo "  make logs-frontend  - View frontend logs"
	@echo "  make clean          - Stop and remove containers, networks, and volumes"
	@echo "  make migrate        - Run database migrations"
	@echo "  make makemigrations - Create new database migrations"
	@echo "  make shell-backend  - Open shell in backend container"
	@echo "  make shell-db       - Open PostgreSQL shell"
	@echo "  make test           - Run all tests"
	@echo "  make test-backend   - Run backend tests"
	@echo "  make test-frontend  - Run frontend tests"
	@echo "  make lint           - Run linting (ruff + pylint)"
	@echo "  make format         - Format code with black and ruff"
	@echo "  make install        - Install dependencies locally"
	@echo "  make dev            - Start development environment"
	@echo "  make setup          - Initial project setup"
	@echo ""

# Docker commands
build:
	@echo "Building Docker containers..."
	docker compose build

start:
	@echo "Starting all services..."
	docker compose up -d

stop:
	@echo "Stopping all services..."
	docker compose down

restart: stop start
	@echo "Services restarted."

logs:
	@echo "Viewing logs from all services..."
	docker compose logs -f

logs-backend:
	@echo "Viewing backend logs..."
	docker compose logs -f backend

logs-frontend:
	@echo "Viewing frontend logs..."
	docker compose logs -f frontend

clean:
	@echo "Cleaning up containers, networks, and volumes..."
	docker compose down -v --remove-orphans
	docker system prune -f

# Database commands
migrate:
	@echo "Running database migrations..."
	docker compose exec backend alembic upgrade head

makemigrations:
	@echo "Creating new database migrations..."
	@if [ -z "$(msg)" ]; then echo "Usage: make makemigrations msg='your message'"; exit 1; fi
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

shell-backend:
	@echo "Opening shell in backend container..."
	docker compose exec backend /bin/bash

shell-db:
	@echo "Opening PostgreSQL shell..."
	docker compose exec db psql -U spendtrack -d spendtrack

# Testing commands
test: test-backend test-frontend
	@echo "All tests completed."

test-backend:
	@echo "Running backend tests..."
	docker compose exec backend pytest

test-frontend:
	@echo "Running frontend tests..."
	docker compose exec frontend npm test

# Code quality commands
lint:
	@echo "Running linting with ruff and pylint..."
	docker compose exec backend ruff check app/
	docker compose exec backend pylint app/

format:
	@echo "Formatting code with black and ruff..."
	docker compose exec backend black app/
	docker compose exec backend ruff format app/
	docker compose exec frontend npm run lint:fix || true

# Development commands
install:
	@echo "Installing backend dependencies..."
	cd backend && pip install uv && uv venv && . .venv/bin/activate && uv pip install -e .
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

dev:
	@echo "Starting development environment..."
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

setup: build
	@echo "Setting up the project for first time use..."
	@echo "1. Building containers..."
	@make build
	@echo "2. Starting services..."
	@make start
	@echo "3. Waiting for services to be ready..."
	@sleep 10
	@echo "4. Running initial migrations..."
	@make migrate || echo "Migrations will run automatically on first start"
	@echo ""
	@echo "✅ Setup complete!"
	@echo ""
	@echo "🌐 Frontend: http://localhost:3000"
	@echo "🔧 Backend API: http://localhost:8000"
	@echo "📚 API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "To view logs: make logs"
	@echo "To stop: make stop"

# Local development without Docker
dev-local:
	@echo "Starting local development servers..."
	@echo "Make sure PostgreSQL, Redis, and Elasticsearch are running locally"
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	cd frontend && npm run dev &
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"

# Utility commands
check-env:
	@echo "Checking environment files..."
	@test -f backend/.env || (echo "❌ backend/.env not found" && exit 1)
	@test -f frontend/.env.local || (echo "❌ frontend/.env.local not found" && exit 1)
	@echo "✅ Environment files found"

seed-data:
	@echo "Processing invoice data..."
	docker compose exec backend python -c "\
import sys; \
sys.path.append('/app'); \
from app.services.invoice_parser import InvoiceParser; \
parser = InvoiceParser(); \
try: \
    expenses = parser.parse_csv_invoice('/app/invoices/fatura-99999999.csv'); \
    print(f'✅ Parsed {len(expenses)} expenses from invoice'); \
    summary = parser.get_summary(expenses); \
    print(f'📊 Total amount: $${summary[\"total_amount\"]}'); \
    print(f'📅 Date range: {summary[\"date_range\"][\"start\"]} to {summary[\"date_range\"][\"end\"]}'); \
except Exception as e: \
    print(f'❌ Error parsing invoice: {e}'); \
"

# Health checks
health:
	@echo "Checking service health..."
	@echo "Backend API:"
	@curl -s http://localhost:8000/health | python -m json.tool || echo "❌ Backend not responding"
	@echo ""
	@echo "Frontend:"
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200" && echo "✅ Frontend responding" || echo "❌ Frontend not responding"
	@echo ""
	@echo "Database:"
	@docker compose exec db pg_isready -U spendtrack && echo "✅ Database ready" || echo "❌ Database not ready"

# Backup and restore
backup:
	@echo "Creating database backup..."
	docker compose exec db pg_dump -U spendtrack spendtrack > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup created: backup_$(shell date +%Y%m%d_%H%M%S).sql"

restore:
	@echo "Restoring database from backup..."
	@read -p "Enter backup file name: " backup_file; \
	docker compose exec -T db psql -U spendtrack spendtrack < $$backup_file

# Update dependencies
update:
	@echo "Updating backend dependencies..."
	cd backend && . .venv/bin/activate && uv pip install --upgrade -r requirements.txt
	@echo "Updating frontend dependencies..."
	cd frontend && npm update