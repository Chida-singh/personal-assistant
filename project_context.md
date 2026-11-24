# Project Context: Personal Assistant (Detailed)

## 1. System Overview
This project is a fully local, AI-powered **Personal Assistant**. It is designed to act as an all-in-one personal operating system to manage tasks, personal notes, finances, calendar events, and secrets. It prioritizes 100% data privacy by keeping all databases, application code, and LLM processing strictly on the host machine. 

## 2. Global Architecture
The system employs a microservices architecture orchestrated via Docker Compose.
- **Frontend**: A modern React SPA communicating via REST.
- **Gateway**: A Go-based reverse proxy that handles JWT authentication and routes traffic to internal microservices.
- **Microservices**: Independent Python/FastAPI services dedicated to specific domains (Todo, Finance, Calendar, Vault, AI).
- **Database**: A single, centralized PostgreSQL database serving the microservices.
- **AI Engine**: A local Ollama instance used for both structured data extraction and conversational chat.

## 3. Frontend Application (`/frontend`)
- **Tech Stack**: React 18, Vite, standard CSS.
- **Port**: `5173`
- **Pages / Modules**:
  - `FinancePage.jsx`: Complex dashboard for visualizing spending, uploading bank statements, and managing transactions.
  - `TodoPage.jsx`: Kanban-style task management.
  - `NotesPage.jsx`: Personal notes and key-value storage.
  - `CalendarPage.jsx`: Google Calendar synchronization and event viewing.
  - `VaultPage.jsx`: Secure, local password management.
  - `ChatPage.jsx`: Conversational interface to interact with the LLM worker.
  - `SettingsPage.jsx`: Global app configuration.

## 4. API Gateway (`/gateway`)
- **Tech Stack**: Go (Gin Framework).
- **Port**: `8000`
- **Responsibilities**:
  - **CORS & Auth**: Enforces JWT-based authentication via an `/api/auth/login` endpoint.
  - **Reverse Proxy**: Routes incoming authenticated requests to internal microservices:
    - `/api/todos/*` & `/api/notes/*` ➔ `todo-service:8001`
    - `/api/finance/*` ➔ `finance-service:8002`
    - `/api/calendar/*` ➔ `calendar-service:8003`
    - `/api/vault/*` ➔ `vault-service:8004`
    - `/api/chat/*` ➔ `llm-worker:8005`

## 5. Microservices (`/services`)
All microservices are built with **Python & FastAPI** and use **SQLModel** for database interactions.

### A. Todo & Notes Service (`todo-service`)
- **Internal Port**: `8001`
- **Key Features**: Manages tasks (with priorities and statuses) and persistent notes/knowledge snippets.
- **Key Endpoints**:
  - `GET|POST /api/todos` (Create/Read tasks)
  - `PUT /api/todos/complete`, `PUT /api/todos/move` (Task state management)
  - `GET|POST /api/notes`, `POST /api/notes/recall` (Note management)

### B. Finance Service (`finance-service`)
- **Internal Port**: `8002`
- **Key Features**: Ingests unstructured bank statements (PDF/CSV), uses Ollama to extract and auto-categorize transactions, and generates analytics.
- **Key Endpoints**:
  - `POST /api/finance/upload`: Handles file uploads and triggers LLM parsing.
  - `GET /api/finance/dashboard`: Returns aggregated stats and chart data (period, category, weekday, balance).
  - `GET /api/finance/transactions`: Paginated/filterable ledger view.
  - `GET /api/finance/charts/{name}`: Serves generated PNG charts for the frontend.

### C. LLM Worker (`llm-worker`)
- **Internal Port**: `8005`
- **Key Features**: The "Brain" of the system. Provides a conversational chat interface and acts as an autonomous agent.
- **Workflow**:
  - Exposes `POST /api/chat` and `POST /api/chat/stream`.
  - Communicates with Ollama to parse user intent.
  - Uses `intent_router.py` to optionally dispatch commands to other services (e.g., automatically creating a Todo item or adding a Calendar event based on natural language).

### D. Calendar Service (`calendar-service`)
- **Internal Port**: `8003`
- **Key Features**: Interacts with the real Google Calendar API via OAuth. OAuth session state is persisted locally via `token.json` volume mount.

### E. Vault Service (`vault-service`)
- **Internal Port**: `8004`
- **Key Features**: Secure local storage of secrets and passwords.

## 6. Database & Storage
- **PostgreSQL Container** (`personal-assistant-db`): Runs on port `5432`. It contains tables for todos, notes, finance ledgers, and vault entries. Data is persisted via the `pgdata` Docker volume.
- **File Storage**: The Finance service stores uploaded bank statements in its local `./data/uploads` directory.

## 7. AI Integration Details
- **Ollama Engine**: The backend assumes Ollama is running on the host machine (`host.docker.internal:11434`).
- **Default Model**: The project defaults to using the `gemma4` model (configurable via `.env` or Docker Compose).
- **Security**: No data is sent to external LLM APIs (like OpenAI or Anthropic). Financial records and personal chat history remain exclusively local.
