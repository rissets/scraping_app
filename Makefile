# Nexus Aggregator - Makefile

.PHONY: help venv install dev prod build stop clean logs test docker-dev docker-prod

# Colors
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

help: ## Show this help message
	@echo "$(BLUE)Nexus Aggregator - Available Commands$(RESET)"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'

# Virtual Environment Commands
venv: ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(RESET)"
	python3 -m venv .venv
	@echo "$(GREEN)Virtual environment created! Activate with: source .venv/bin/activate$(RESET)"

install: ## Install dependencies in virtual environment
	@echo "$(BLUE)Installing dependencies...$(RESET)"
	./.venv/bin/pip install --upgrade pip
	./.venv/bin/pip install -r requirements.txt
	@echo "$(GREEN)Dependencies installed!$(RESET)"

# Development Commands
dev: ## Run development server locally
	@echo "$(BLUE)Starting development server...$(RESET)"
	./.venv/bin/python main.py

test: ## Run API tests
	@echo "$(BLUE)Running API tests...$(RESET)"
	./.venv/bin/python tests/test_api.py

# Docker Commands
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(RESET)"
	cd docker && docker build -t nexus-aggregator:latest -f Dockerfile ..
	@echo "$(GREEN)Docker image built successfully!$(RESET)"

docker-dev: ## Start development environment with Docker
	@echo "$(BLUE)Starting development environment with Docker...$(RESET)"
	cd docker && docker-compose -f docker/docker-compose.dev.yml up -d

docker-prod: ## Start production environment with Docker
	@echo "$(BLUE)Starting production environment with Docker...$(RESET)"
	cd docker && docker-compose -f docker/docker-compose.prod.yml up -d

docker-stop: ## Stop Docker containers
	@echo "$(BLUE)Stopping Docker containers...$(RESET)"
	cd docker && docker-compose down

docker-clean: ## Clean Docker containers and volumes
	@echo "$(YELLOW)Cleaning Docker containers and volumes...$(RESET)"
	cd docker && docker-compose down --volumes --remove-orphans
	docker system prune -f

docker-logs: ## Show Docker container logs
	@echo "$(BLUE)Showing Docker logs...$(RESET)"
	cd docker && docker-compose logs -f

docker-test: ## Run tests against Docker container
	@echo "$(BLUE)Running tests against Docker container...$(RESET)"
	./venv/bin/python tests/test_api.py

# Setup Commands
setup-local: venv install ## Complete local setup (venv + install)
	@echo "$(GREEN)Local setup completed!$(RESET)"
	@echo "$(BLUE)Next steps:$(RESET)"
	@echo "1. Activate virtual environment: $(YELLOW)source .venv/bin/activate$(RESET)"
	@echo "2. Start development server: $(YELLOW)make dev$(RESET)"
	@echo "3. Open API docs: $(YELLOW)http://localhost:8000/docs$(RESET)"

setup-docker: docker-build ## Setup Docker environment
	@echo "$(GREEN)Docker setup completed!$(RESET)"
	@echo "$(BLUE)Next steps:$(RESET)"
	@echo "1. Start development: $(YELLOW)make docker-dev$(RESET)"
	@echo "2. Start production: $(YELLOW)make docker-prod$(RESET)"
	@echo "3. Open API docs: $(YELLOW)http://localhost:8000/docs$(RESET)"

# Utility Commands
clean-python: ## Clean Python cache files
	@echo "$(BLUE)Cleaning Python cache files...$(RESET)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	@echo "$(GREEN)Python cache cleaned!$(RESET)"

format: ## Format code with black (if installed)
	@echo "$(BLUE)Formatting code...$(RESET)"
	@if [ -f "./.venv/bin/black" ]; then \
		./.venv/bin/black . --line-length 100; \
		echo "$(GREEN)Code formatted!$(RESET)"; \
	else \
		echo "$(YELLOW)Black not installed. Install with: pip install black$(RESET)"; \
	fi

# Documentation Commands
docs-validate: ## Validate OpenAPI specification
	@echo "$(BLUE)Validating OpenAPI specification...$(RESET)"
	./scripts/validate-openapi.sh

docs-demo: ## Run documentation demo
	@echo "$(BLUE)Running documentation demo...$(RESET)"
	./scripts/demo-docs.sh

docs-serve: ## Open API documentation in browser (requires API server running)
	@echo "$(BLUE)Opening API documentation...$(RESET)"
	@echo "$(GREEN)Swagger UI:$(RESET) http://localhost:8000/docs"
	@echo "$(GREEN)ReDoc:$(RESET) http://localhost:8000/redoc"
	@echo "$(GREEN)Custom UI:$(RESET) docs/swagger-ui.html"
	@if command -v xdg-open > /dev/null; then \
		xdg-open http://localhost:8000/docs; \
	elif command -v open > /dev/null; then \
		open http://localhost:8000/docs; \
	else \
		echo "$(YELLOW)Please open http://localhost:8000/docs manually$(RESET)"; \
	fi

docs-generate: ## Generate client libraries (requires openapi-generator-cli)
	@echo "$(BLUE)Generating client libraries...$(RESET)"
	@if command -v openapi-generator-cli > /dev/null; then \
		mkdir -p clients; \
		openapi-generator-cli generate -i openapi.yaml -g python -o clients/python; \
		openapi-generator-cli generate -i openapi.yaml -g javascript -o clients/javascript; \
		echo "$(GREEN)Client libraries generated in clients/ directory$(RESET)"; \
	else \
		echo "$(YELLOW)openapi-generator-cli not found. Install with:$(RESET)"; \
		echo "npm install -g @openapitools/openapi-generator-cli"; \
	fi

# Default target
all: help
