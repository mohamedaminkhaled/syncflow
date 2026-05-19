# Makefile — SyncFlow local development
# Requires: Docker Compose v2+

COMPOSE := docker compose
PROJECT := syncflow

.PHONY: help up down build logs migrate makemigrations shell test lint format ci psql redis-cli clean

## help: Show this help message
help:
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

## up: Start all services in detached mode
up:
	$(COMPOSE) up --build -d
	@echo "Waiting for healthchecks..."
	@sleep 3
	$(COMPOSE) ps

## down: Stop and remove containers, keep named volumes
down:
	$(COMPOSE) down

## build: Rebuild the web image (useful after Dockerfile changes)
build:
	$(COMPOSE) build web

## logs: Tail logs from all services
logs:
	$(COMPOSE) logs -f

## migrate: Run Django migrations
migrate:
	$(COMPOSE) exec web python manage.py migrate

## makemigrations: Generate Django migrations
makemigrations:
	$(COMPOSE) exec web python manage.py makemigrations

## shell: Open Django shell inside the web container
shell:
	$(COMPOSE) exec web python manage.py shell

## test: Run Django tests with warnings as errors
test:
	$(COMPOSE) exec web python manage.py test --verbosity=2

## lint: Run Ruff linter (install Ruff in Dockerfile or add via uv)
lint:
	$(COMPOSE) exec web ruff check .

## format: Run Ruff formatter (or Black)
format:
	$(COMPOSE) exec web ruff format .

## ci: Run the full CI pipeline locally — lint + check + test
ci: lint
	$(COMPOSE) exec web python manage.py check --deploy --fail-level ERROR
	$(COMPOSE) exec web python manage.py test

## psql: Open Postgres CLI inside the db container
psql:
	$(COMPOSE) exec db psql -U postgres -d syncflow

## redis-cli: Open Redis CLI inside the redis container
redis-cli:
	$(COMPOSE) exec redis redis-cli

## clean: Stop everything and delete named volumes (DESTRUCTIVE)
clean:
	$(COMPOSE) down -v --remove-orphans
