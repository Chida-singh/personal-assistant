# Personal Assistant (Microservices Architecture)

## What This Is
This is a local AI-powered personal assistant designed to help you manage your tasks, finances, calendar, and secrets entirely locally. It features a modern **React (Vite)** frontend communicating with a high-performance **Go API Gateway**, which routes traffic to a suite of independent **FastAPI (Python)** microservices. It leverages **Ollama** for entirely private, local LLM processing (such as extracting structured data from unstructured bank PDFs and powering conversational interfaces). All structured data is persisted in a unified **PostgreSQL** database.

## Architecture

The system is broken down into the following Dockerized services:

1. **Frontend (`frontend/`)**: React + Vite application running on port `5173`.
2. **API Gateway (`gateway/`)**: A Go/Gin reverse proxy handling JWT authentication and routing on port `8000`.
3. **Todo Service (`services/todo-service/`)**: Manages tasks and personal notes.
4. **Finance Service (`services/finance-service/`)**: Parses bank statements using Ollama, auto-categorizes, and generates spending insights and charts.
5. **Calendar Service (`services/calendar-service/`)**: Interfaces with Google Calendar OAuth to check, create, and modify events.
6. **Vault Service (`services/vault-service/`)**: A secure local password and secret manager.
7. **LLM Worker (`services/llm-worker/`)**: The "Brain" orchestrator that chats with the user, determines intent using Ollama, and fulfills requests by communicating with the other internal microservices.
8. **PostgreSQL (`personal-assistant-db`)**: The central relational database for all services.

## Features
- **Local LLM Bank Statement Parsing:** Drag and drop PDFs or CSVs of your bank statements. Ollama processes them locally and categorizes every transaction.
- **Dynamic Dashboards:** Visualize your spending, cash flow, and top merchants automatically.
- **Global Assistant Memory (The "Brain"):** Chat naturally with your assistant to add tasks, query your calendar, remember specific details, or just chat.
- **Calendar Sync:** Connect directly to your real Google Calendar.
- **100% Private Data:** No financial data ever leaves your machine. Your data is stored in the local Dockerized PostgreSQL instance.

---

## Prerequisites
- **Docker** and **Docker Compose**
- **Node.js 18+** (for running the frontend locally)
- **Ollama** installed and running on your host machine.
- If you want to use Claude Code with a local GGUF model, see [docs/claude-code-ollama-windows.md](docs/claude-code-ollama-windows.md).
- If you prefer a one-click workflow, use [scripts/setup-claude-code-ollama.cmd](scripts/setup-claude-code-ollama.cmd) or the VS Code task added under `.vscode/tasks.json`.
- If you want a browser UI for the same local model, use Open WebUI with [docker-compose.open-webui.yml](docker-compose.open-webui.yml).

## Setup Instructions

### 1. Setup Ollama
The backend relies on Ollama to parse financial data and determine user intents. Ensure Ollama is running on your host machine and you have pulled your preferred model (default is `gemma4`, but you can update `docker-compose.yml` to specify others).

```powershell
# Open a terminal
ollama serve

# If you haven't already pulled a model
ollama pull gemma4
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory (you can copy `.env.example`). 

```env
# Google Calendar (Optional)
GOOGLE_CLIENT_ID="your_oauth_client_id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your_oauth_client_secret"
GOOGLE_REDIRECT_URI="http://localhost:5173"
```

### 2b. Optional: Add a local chat UI
If you want a simple Claude-like browser interface for your local GGUF model, first create the Ollama model and then start Open WebUI:

```powershell
# Create the Ollama model from your GGUF file
.\scripts\setup-claude-code-ollama.ps1 -GgufPath "D:\Downloads\yuxinlu1-gemma-4-12B-coder-fable5-composer2.5-v1-GGUF.gguf" -ModelName gemma-coder

# Start the browser UI
docker compose -f docker-compose.open-webui.yml up -d
```

Then open `http://localhost:3000`.

### 3. Build & Run the Microservices
We use Docker Compose to orchestrate the PostgreSQL database, the Go API Gateway, and all Python microservices.

```powershell
# Navigate to the workspace root
cd D:\Chida\Projects\personal-assistant

# Build and start all containers in detached mode
docker compose up --build -d
```
*The Go API Gateway will be available at `http://localhost:8000`, routing securely to the internal microservices.*

### 4. Install & Run the Frontend
The frontend is a modern React SPA built with Vite. It is configured to automatically fetch a JWT token from the Gateway and attach it to requests.

```powershell
# Open a new terminal
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```
*The frontend will be available at `http://localhost:5173`. Open this in your browser to start using the app!*

---

## Privacy & Security
- **Database:** All structured data is stored inside a Docker volume (`pgdata`).
- **OAuth Tokens:** Google OAuth tokens are volume-mounted via `token.json` so you do not lose your session when containers restart.
- Ensure you do not commit any `.env` or `token.json` files containing actual secrets.

Built a local LLM-powered finance service processing X PDFs and generating Y reports with sub-second retrieval latency."