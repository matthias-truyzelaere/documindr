.PHONY: up down build

# Start all services
up:
	docker compose up -d

# Stop all services
down:
	docker compose down

# Rebuild all services
build: down
	docker compose up -d --build