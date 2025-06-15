.PHONY: help setup install build test clean docker-build docker-up docker-down lint format

# Default target
help:
	@echo "BitterBot Unified AGI Platform - Available Commands:"
	@echo "  make setup          - Set up development environment"
	@echo "  make install        - Install all dependencies"
	@echo "  make build          - Build all components"
	@echo "  make test           - Run all tests"
	@echo "  make clean          - Clean build artifacts"
	@echo "  make docker-build   - Build Docker images"
	@echo "  make docker-up      - Start all services"
	@echo "  make docker-down    - Stop all services"
	@echo "  make lint           - Run linters"
	@echo "  make format         - Format code"
	@echo "  make health-check   - Check system health"

# Setup development environment
setup:
	@echo "Setting up development environment..."
	cp .env.example .env
	python -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt
	cd src/protocol_layer && cargo build
	@echo "Setup complete!"

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "Installing Rust dependencies..."
	cd src/protocol_layer && cargo fetch
	@echo "Dependencies installed!"

# Build all components
build: build-python build-rust build-docker

build-python:
	@echo "Building Python components..."
	python -m py_compile src/**/*.py

build-rust:
	@echo "Building Rust components..."
	cd src/protocol_layer && cargo build --release

build-docker:
	@echo "Building Docker images..."
	docker-compose build

# Run tests
test: test-unit test-integration

test-unit:
	@echo "Running unit tests..."
	pytest tests/unit -v

test-integration:
	@echo "Running integration tests..."
	pytest tests/integration -v

test-e2e:
	@echo "Running end-to-end tests..."
	pytest tests/e2e -v

test-performance:
	@echo "Running performance tests..."
	pytest tests/performance -v

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	cd src/protocol_layer && cargo clean
	@echo "Clean complete!"

# Docker operations
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting all services..."
	docker-compose up -d

docker-down:
	@echo "Stopping all services..."
	docker-compose down

docker-logs:
	docker-compose logs -f

# Code quality
lint: lint-python lint-rust

lint-python:
	@echo "Linting Python code..."
	flake8 src tests
	mypy src tests
	black --check src tests

lint-rust:
	@echo "Linting Rust code..."
	cd src/protocol_layer && cargo clippy -- -D warnings

format: format-python format-rust

format-python:
	@echo "Formatting Python code..."
	black src tests
	isort src tests

format-rust:
	@echo "Formatting Rust code..."
	cd src/protocol_layer && cargo fmt

# Health check
health-check:
	@echo "Checking system health..."
	curl -f http://localhost:8000/health || echo "API Gateway is not running"
	curl -f http://localhost:9001/health || echo "Orchestrator is not running"
	curl -f http://localhost:9090/metrics || echo "Prometheus is not running"
	@echo "Health check complete!"

# Development shortcuts
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

dev-api:
	cd src/integration_layer/api_gateway && uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-orchestrator:
	cd src/protocol_layer && cargo run --bin orchestrator

dev-worker:
	cd src/protocol_layer && cargo run --bin worker

# Database operations
db-migrate:
	alembic upgrade head

db-rollback:
	alembic downgrade -1

db-reset:
	alembic downgrade base && alembic upgrade head