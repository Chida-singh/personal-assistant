# Personal Assistant

## What This Is
This is a local AI-powered personal assistant designed to help you manage your finances, calendar, and notes entirely locally. It features a modern **React (Vite)** frontend and a high-performance **FastAPI (Python)** backend, leveraging **Ollama** for entirely private, local LLM processing (such as extracting structured data from unstructured bank PDFs).

## Features
- **Local LLM Bank Statement Parsing:** Drag and drop PDFs or CSVs of your bank statements. Ollama processes them locally and categorizes every transaction.
- **Dynamic Dashboards:** Visualize your spending, cash flow, and top merchants automatically.
- **Calendar & Notes:** Integrated lightweight modules for productivity.
- **100% Private:** No financial data ever leaves your machine. Your data is stored in local JSON files inside `backend/data/`.

---

## Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **Ollama** installed and running on your system.

## Setup Instructions

### 1. Install & Run the Backend
The backend handles API requests, database (JSON) interactions, and orchestrates calls to Ollama.

```powershell
# Navigate to the workspace root
cd backend

# Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # On macOS/Linux use `source .venv/bin/activate`

# Install requirements
pip install -r requirements.txt

# Run the FastAPI server
uvicorn main:app --reload --port 8000
```
*The backend will be available at `http://localhost:8000`.*

### 2. Setup Ollama
The backend relies on Ollama to parse financial data. Ensure Ollama is running and you have pulled your preferred model (default is `llama3`, but you can update `.env` to specify `gemma` or others).

```powershell
# Open a new terminal
ollama serve

# If you haven't already pulled a model
ollama pull llama3
```

### 3. Install & Run the Frontend
The frontend is a modern React SPA built with Vite.

```powershell
# Open a third terminal
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```
*The frontend will be available at `http://localhost:5173`. Open this in your browser to start using the app!*

---

## Configuration & Environment Variables
Create a `.env` file in the root directory (you can copy `.env.example`). 

```env
# Google Calendar (Optional)
GOOGLE_API_KEY="your_google_api_key_here"
GOOGLE_CLIENT_ID="your_oauth_client_id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your_oauth_client_secret"
GOOGLE_REDIRECT_URI="http://localhost:5173"
```

## Privacy & Security
This project is configured to be GitHub-push friendly:
- The `backend/data/` folder is strictly ignored in `.gitignore`, ensuring your `finance_ledger.json` and any uploaded PDFs are never committed to version control.
- Ensure you do not commit any `.env` files containing actual secrets.