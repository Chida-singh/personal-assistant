# Personal Assistant

## What This Is
This is a local desktop AI assistant built with PySide6, Ollama, and optional Google Calendar integration.

## Prerequisites
- Windows PowerShell
- Python 3.10+
- Ollama installed and available in PATH

## Project Paths
- Workspace root: `D:\Chida\Projects\personal-assistant`
- App folder: `D:\Chida\Projects\personal-assistant\assistant`

## Environment Variables
Create or update `.env` in the workspace root with:

```env
GOOGLE_API_KEY="your_google_api_key"
GOOGLE_CLIENT_ID="your_oauth_client_id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your_oauth_client_secret"
GOOGLE_REDIRECT_URI="http://localhost"
```

Notes:
- Google Calendar event creation/checking uses OAuth credentials.
- `GOOGLE_API_KEY` is optional for Calendar API client initialization in this codebase.

## First-Time Setup
Run these commands in PowerShell.

```powershell
cd D:\Chida\Projects\personal-assistant
python -m venv .venv
.\.venv\Scripts\activate

cd assistant
pip install -r requirements.txt
ollama pull llama3
```

## Run The App (Recommended: 2 Terminals)

### Terminal A (Ollama)
```powershell
cd D:\Chida\Projects\personal-assistant
ollama serve
```

### Terminal B (Desktop App)
```powershell
cd D:\Chida\Projects\personal-assistant\assistant
..\.venv\Scripts\python.exe main.py
```

## If You See This Error
`Error: listen tcp 127.0.0.1:11434: bind ...`

That means Ollama is already running. Do not start `ollama serve` again. Just open a new terminal and launch the app.

You can verify Ollama is alive with:

```powershell
ollama list
```

## Optional: Restart Ollama
Only do this if Ollama is stuck.

```powershell
netstat -ano | findstr :11434
taskkill /PID <PID> /F
ollama serve
```

## Quick Start (After Initial Setup)
```powershell
cd D:\Chida\Projects\personal-assistant\assistant
..\.venv\Scripts\python.exe main.py
```