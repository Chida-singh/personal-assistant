# Personal Assistant — Master TODO

> **Vision:** A fully self-hosted, all-in-one personal productivity hub —
> accessible from any device, always on, 100% under your control.

---

## 🏗️ Target Architecture (Locked In)

```
Your Phone / Laptop / Any device
          │
          │  HTTPS (free SSL via Let's Encrypt)
          ▼
 ┌─────────────────────────────────────┐
 │   Google Cloud e2-micro VM          │
 │   (free forever — us-west1)         │
 │                                     │
 │   Nginx  →  FastAPI  →  SQLite      │
 │                                     │
 │   All data lives here:              │
 │   • Habits & streaks                │
 │   • Todos & due dates               │
 │   • Calendar events                 │
 │   • Journal / mood logs             │
 │   • Notes                           │
 │   • Finance transactions            │
 │   • Vault (encrypted at rest)       │
 └─────────────────────────────────────┘
          │
          │  Gemini API (free tier) — AI fallback
          ▼
   Google Gemini Flash
   (used when Ollama not available)
```

**Key decisions:**
- ✅ Google Cloud e2-micro VM — free, 24/7, public IP, no Tailscale needed
- ✅ HTTPS via Caddy or Let's Encrypt — encrypted in transit
- ✅ JWT login — only you can access the app
- ✅ Vault encrypted with master password (Fernet) — safe even if VM is compromised
- ✅ Ollama on local PC only — for dev/testing, never required for production
- ✅ Gemini API (free tier) — AI in production on the VM
- ✅ Vercel — hosts the React frontend (free, global CDN)
- ❌ No Tailscale needed
- ❌ No VPS cost

---

## 🔴 PHASE 1 — Infrastructure (Do This First)

### 1.1 — Provision the Google Cloud VM
- [ ] Create a Google Cloud account (requires credit card — won't be charged)
- [ ] Create an e2-micro VM instance:
  - Region: `us-west1` (Oregon) — required for free tier
  - Machine type: `e2-micro`
  - Boot disk: 30 GB Standard persistent disk (HDD, not SSD)
  - OS: Ubuntu 22.04 LTS
- [ ] Set up SSH key access (disable password login)
- [ ] Configure firewall rules: allow ports 80, 443 (HTTP/HTTPS) only
- [ ] Reserve a static external IP address (free while attached to running VM)
- [ ] Point a domain or subdomain to the VM IP (optional — use free `.duckdns.org` if no domain)

### 1.2 — Set Up the VM Environment
- [ ] SSH into VM and install: `python3`, `pip`, `git`, `nginx` or `caddy`
- [ ] Clone the repo onto the VM
- [ ] Create Python virtual environment, `pip install -r requirements.txt`
- [ ] Set up **Caddy** (easiest HTTPS) — auto-renews Let's Encrypt SSL for free
  ```
  caddy reverse-proxy --from yourdomain.com --to localhost:8000
  ```
- [ ] Create a `systemd` service for FastAPI — auto-starts on VM reboot:
  ```ini
  [Service]
  ExecStart=/path/to/.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
  Restart=always
  ```
- [ ] Set environment variables in `/etc/environment` or a `.env` file (not in repo):
  - `GEMINI_API_KEY`
  - `JWT_SECRET`
  - `VAULT_MASTER_KEY_HINT` (reminder only — key derived at runtime)

### 1.3 — Migrate Data Storage: JSON → SQLite
> JSON files are fine for dev. SQLite is safer for production (concurrent writes, no corruption risk).

- [ ] Add `sqlalchemy` + `aiosqlite` to `requirements.txt`
- [ ] Create `backend/core/database.py` — SQLAlchemy async engine pointing to `data/app.db`
- [ ] Migrate each module to use SQLite tables instead of JSON files:
  - `todos.json` → `todos` table
  - `girlfriend.json` → `notes` table
  - `finance_ledger.json` → `transactions` table
  - `vault.json` → `vault` table
  - `events` (calendar) → `events` table
- [ ] Write `migrate_json_to_sqlite.py` — one-time script to import existing JSON into SQLite
- [ ] Keep JSON export working (for backups)

### 1.4 — Authentication (Only You Can Access It)
- [ ] Add `python-jose` and `passlib` to `requirements.txt`
- [ ] Create `backend/core/auth.py` — JWT token generation + verification
- [ ] Add `POST /api/auth/login` endpoint (username + password → JWT token)
- [ ] Store your credentials in `.env` (never hardcoded)
- [ ] Add auth middleware — protect all `/api/*` routes except `/api/health` and `/api/auth/login`
- [ ] Create `frontend/src/pages/LoginPage.jsx` — simple login form
- [ ] Store JWT in `localStorage`, attach as `Authorization: Bearer <token>` header on all API calls
- [ ] Add logout button in `SettingsPage.jsx`
- [ ] Token expiry: 30 days (refresh on activity)

### 1.5 — Smart AI Fallback (Ollama → Gemini)
> Ollama won't run on the VM (not enough RAM). Gemini Flash free tier is the AI on production.

- [ ] On startup, check if Ollama is reachable (`GET http://localhost:11434/api/tags`)
- [ ] If Ollama available → use Ollama (local dev mode)
- [ ] If Ollama unavailable → switch to **Gemini Flash API** automatically
- [ ] Wrap both in a single `llm_call(prompt)` function in `backend/core/llm.py`
- [ ] Update `/api/health` to return `{ llm_source: "ollama" | "gemini" | "offline" }`
- [ ] Update `SettingsPage.jsx` to show which AI is active
- [ ] Add `GEMINI_API_KEY` to `.env.example` with setup instructions

### 1.6 — Deploy Frontend to Vercel
- [ ] Run `npm run build` in `/frontend` → generates `frontend/dist/`
- [ ] Create a Vercel account, connect GitHub repo
- [ ] Set build output to `frontend/dist`, root to `frontend/`
- [ ] Add environment variable in Vercel: `VITE_API_BASE_URL=https://yourdomain.com`
- [ ] Update `frontend/src/api.js` to use `VITE_API_BASE_URL` env variable
- [ ] Every `git push` → Vercel auto-redeploys the frontend

---

## 🟡 PHASE 2 — New Modules

### 2.1 — Habit Tracker *(new feature)*
**Backend:**
- [ ] Create `backend/modules/habits.py`
- [ ] Habit model: `{ id, name, description, frequency: daily|weekly, target_days[], created_at }`
- [ ] Log model: `{ habit_id, date, completed, note }`
- [ ] API endpoints:
  - `GET /api/habits` — list all habits
  - `POST /api/habits` — create habit
  - `POST /api/habits/{id}/log` — mark done/undone for a date
  - `GET /api/habits/{id}/streak` — current streak + longest streak
  - `GET /api/habits/today` — today's habits + completion %
  - `DELETE /api/habits/{id}`

**Frontend:**
- [ ] Create `frontend/src/pages/HabitsPage.jsx`
- [ ] Today's habits as checkboxes — tap to mark done
- [ ] Streak counter per habit (🔥 7 days)
- [ ] Weekly heatmap grid (like GitHub contributions)
- [ ] Add to `App.jsx` routes and `Sidebar.jsx`

**AI:**
- [ ] Add `track_habit` and `habit_summary` intents to chat assistant

---

### 2.2 — Dashboard / Home Screen *(new feature)*
> Replace the AI chat as the default home screen. Chat moves to `/chat`.

- [ ] Create `frontend/src/pages/DashboardPage.jsx`
- [ ] Make Dashboard the default route `/`, move Chat to `/chat`
- [ ] Dashboard widgets:
  - [ ] 🕐 Date + greeting ("Good morning, Chida")
  - [ ] ✅ Habits due today (quick-check inline)
  - [ ] 📋 Todos due today + overdue count
  - [ ] 📅 Next 3 calendar events
  - [ ] 💰 This month's spend vs last month (single number)
  - [ ] 📔 Mood streak + "How are you feeling?" prompt

---

### 2.3 — Journal / Daily Log *(new feature)*
**Backend:**
- [ ] Create `backend/modules/journal.py`
- [ ] Entry model: `{ id, date, mood: 1-5, entry: str, tags[], created_at }`
- [ ] API endpoints:
  - `GET /api/journal` — list entries (paginated)
  - `POST /api/journal` — create/update today's entry
  - `GET /api/journal/{date}` — entry for a date
  - `GET /api/journal/stats` — mood trend last 30 days

**Frontend:**
- [ ] Create `frontend/src/pages/JournalPage.jsx`
- [ ] Today's entry textarea (auto-saves on blur)
- [ ] Mood picker (1–5 emoji scale 😞😕😐🙂😄)
- [ ] Past entries list with mood colour coding
- [ ] Mood trend mini line chart (30 days)

---

### 2.4 — Enhanced Todos (Upgrade Existing)
- [ ] Add `due_date`, `tags[]`, `created_at`, `updated_at` to todo model
- [ ] `GET /api/todos/due-today` and `GET /api/todos/overdue` endpoints
- [ ] Tag filtering: `GET /api/todos?tag=work`
- [ ] `TodoPage.jsx` — show due date badges + red highlight for overdue
- [ ] Add date picker + tag input to create/edit form
- [ ] "Due Today" and "Overdue" sections pinned to top of list

---

### 2.5 — Calendar Polish (Upgrade Existing)
- [ ] Fix Google OAuth for headless server (pre-generate refresh token, store in `.env`)
- [ ] Add local calendar fallback (`events.json` / SQLite) for when Google isn't configured
- [ ] Add week view to `CalendarPage.jsx`
- [ ] Click on day → event detail / create modal
- [ ] Add recurring events (daily, weekly, monthly)

---

### 2.6 — Notes Upgrade (Upgrade Existing)
- [ ] Rename `girlfriend.py` → `notes.py`, `GIRLFRIEND_FILE` → `NOTES_FILE` (update all imports)
- [ ] Upgrade from key-value → rich notes: `{ id, title, body, tags[], pinned, created_at, updated_at }`
- [ ] Add `GET /api/notes/search?q=` for full-text search
- [ ] `NotesPage.jsx` — grid of note cards (like Apple Notes)
- [ ] Markdown rendering in note body
- [ ] Pin important notes to top

---

## 🟢 PHASE 3 — Security & Polish

### 3.1 — Vault Encryption (High Priority)
> Vault currently stores passwords in plaintext. Fix this before going to production.

- [ ] Add `cryptography` to `requirements.txt`
- [ ] On vault read/write: encrypt/decrypt with Fernet using a key derived from master password (PBKDF2)
- [ ] Master password entered at login — key derived in memory, never stored
- [ ] `VaultPage.jsx` — add "Unlock Vault" step (enter master password separately from app login)
- [ ] Add password strength indicator when adding entries
- [ ] Add TOTP/2FA code field support

### 3.2 — Progressive Web App (PWA)
> Install on phone home screen — feels like a native app.

- [ ] Add `vite-plugin-pwa` to frontend
- [ ] Create `manifest.json` with app name, icon, theme colour
- [ ] Service Worker — cache static assets for offline view
- [ ] Add "Add to Home Screen" install prompt

### 3.3 — Finance Improvements
- [ ] Fix: use rule-based keyword matching as primary categorisation, AI only for ambiguous
- [ ] Add budget goals per category (e.g. Food: ₹5,000/month)
  - [ ] `POST /api/finance/budgets`
  - [ ] Budget vs actual bar chart on Finance dashboard
- [ ] Export transactions to CSV from the UI
- [ ] Recurring expense detection

### 3.4 — Backup & Export
- [ ] `GET /api/export` → returns a zip of all data as JSON
- [ ] "Download Backup" button in `SettingsPage.jsx`
- [ ] `POST /api/import` → restore from a backup zip
- [ ] Auto-backup: daily SQLite dump to a configured folder

### 3.5 — AI Chat Upgrade
- [ ] Cross-module queries: "What tasks do I have this week?" → query todos + calendar
- [ ] "How much did I spend this month?" → query finance module
- [ ] "What habits did I miss?" → query habits module
- [ ] Voice input (Web Speech API) in `ChatPage.jsx`
- [ ] Chat history persistence in SQLite

---

## 📱 Current State of the App

| Module | Backend | Frontend | Status |
|---|---|---|---|
| Chat / AI | ✅ | ✅ | Working — needs Gemini fallback |
| Finance | ✅ | ✅ | Working — Ollama-dependent |
| Todos | ✅ | ✅ | Working — needs due dates/tags |
| Notes | ✅ | ✅ | Working — needs upgrade |
| Calendar | ✅ | ✅ | Working — Google OAuth fragile |
| Vault | ✅ | ✅ | Working — ⚠️ plaintext risk |
| **Habits** | ❌ | ❌ | Not built yet |
| **Journal** | ❌ | ❌ | Not built yet |
| **Dashboard** | ❌ | ❌ | Not built yet |

---

*Last updated: 2026-11-19*
