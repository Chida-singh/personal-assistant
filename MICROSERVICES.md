# Microservices Design & Local Dev Guide

Concise plan to convert this repo into a scalable microservices layout and local dev setup.

## Goals
- Split responsibilities so services can be scaled independently.
- Use PostgreSQL for durable storage (replace local JSON files).
- Containerize each service with Docker; use `docker-compose` for local orchestration.
- Keep Ollama as a dedicated LLM worker service.

## Recommended Service Boundaries
- `api-gateway` — single entrypoint (routes requests, auth, proxy to services).
- `finance-service` — handles statement parsing, ledger, transactions.
- `calendar-service` — calendar events and syncing.
- `todo-service` — todo items and notes.
- `vault-service` — encrypted secrets / attachments storage.
- `llm-worker` — Ollama integration for parsing/classification tasks.
- `storage-service` (optional) — object store abstraction if attachments grow.

Tech stack per service: FastAPI (Python) + PostgreSQL + Docker. Services expose OpenAPI specs.

## Local architecture
- Each service runs in its own container, connected to a Postgres container.
- `api-gateway` routes to internal service ports (no public exposure except gateway).
- `llm-worker` runs alongside Ollama (or calls Ollama API endpoint if remote).

## Migration notes
- Replace `backend/data/*.json` with Postgres schemas per service.
- Implement a thin data migration script to import existing JSON into Postgres.
- Introduce repository/adapters following hexagonal (ports & adapters) per service.

## Docker & Local Dev (high level)
1. Add `Dockerfile` to each service.
2. Add `docker-compose.yml` at repo root with services: `postgres`, `api-gateway`, each microservice, and `llm-worker`.
3. Use environment files `.env.<service>` for secrets; do NOT commit them.
4. Health checks: `/health` for each service; gateway checks before routing.

Example local commands (when files added):
```powershell
cd d:\Chida\Projects\personal-assistant
docker compose up --build
```

## Postgres guidance
- Use one Postgres instance for local dev; in production prefer one DB per service or schema-per-service.
- Create migrations using `alembic` or `sqlmodel`+`sqlalchemy` migrations.

## OpenAPI
- API contracts should live under `/openapi/*.yaml` per service. Use these for gateway routing and client generation.

## Next steps (recommended)
1. Scaffold service folders: `services/finance`, `services/calendar`, `services/todo`, `services/vault`, `services/llm-worker`, `gateway/`.
2. Add `Dockerfile` and minimal FastAPI app for each service exposing `/health` and one example endpoint.
3. Add `docker-compose.yml` and a `Makefile` or `dev.ps1` for common commands.
4. Migrate JSON -> Postgres and add migrations.
5. Refactor services to hexagonal architecture (domain layer, ports, adapters, infra).

Keep this file short; implementation details belong in each service README.
