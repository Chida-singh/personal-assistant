# Personal Assistant — Master TODO

> **Vision:** A fully self-hosted, all-in-one personal productivity hub —
> accessible from anywhere, works offline-first, keeps data 100% private.
> AI runs locally (Ollama) when available, falls back to free cloud APIs when not.

---

## 🔴 PHASE 1 — Foundation (Do This First)

### 1.1 — Smart AI Fallback (Ollama → Free Cloud API)
> Currently the app crashes or fails silently if Ollama isn't running.
> Fix: auto-detect Ollama, fall back to a free online model if it's not available.

- [ ] Add Ollama health check in `backend/main.py` on startup (`GET http://localhost:11434/api/tags`)
- [ ] If Ollama is offline → automatically switch to **Google Gemini Flash free tier** (via `GEMINI_API_KEY` in `.env`)
- [ ] Add `GEMINI_API_KEY` to `.env.example` with instructions
- [ ] Add `/api/health` response to include `llm_source: "ollama" | "gemini" | "offline"`
- [ ] Update `SettingsPage.jsx` to show which AI is currently active (Ollama local / Gemini cloud / offline)
- [ ] Remove Ollama from Task Scheduler / always-on setup — only run it on-demand

**Free cloud model options (ranked):**
1. Google Gemini Flash — `gemini-1.5-flash` (generous free quota)
2. Groq API — `llama-3.1-8b-instant` (very fast, free tier)
3. OpenRouter — routes to multiple free models

---

### 1.2 — Internet Access (Always-On Deployment)
> Currently only works on localhost. Need to access from phone, other laptops, etc.

**Option A — Self-hosted on your PC (Recommended if PC is always on):**
- [ ] Install **Tailscale** on your PC and all devices (free, private VPN mesh)
- [ ] Build frontend for production: `npm run build` in `/frontend`
- [ ] Install **Nginx** on Windows → serve `frontend/dist` on port 80
- [ ] Configure Nginx to proxy `/api/*` → `http://127.0.0.1:8000`
- [ ] Update `backend/main.py` CORS to allow Tailscale origins
- [ ] Add 3 Windows Task Scheduler tasks (auto-start on boot): FastAPI, Nginx
- [ ] Enable **MagicDNS** in Tailscale → get stable hostname like `my-pc.tail1234.ts.net`

**Option B — VPS (if PC isn't always on):**
- [ ] Provision a cheap VPS (Oracle Free Tier / Hetzner CX11 ~€4/mo)
- [ ] Deploy FastAPI + Nginx on VPS, frontend as static files
- [ ] Use **Cloudflare Tunnel** (free) or Caddy for HTTPS
- [ ] Data stored on VPS (no Ollama — use Gemini API instead for AI)

---

### 1.3 — Authentication (Only You Can Access It)
- [ ] Add simple **HTTP Basic Auth** in Nginx (1 username + hashed password) **OR**
- [ ] Add a FastAPI login endpoint with JWT token stored in `localStorage`
- [ ] Protect all `/api/*` routes with the token
- [ ] Add a login page in React (simple username + password form)
- [ ] On mobile, save to Home Screen for a native app-like experience

---

## 🟡 PHASE 2 — New Modules (Build These Next)

### 2.1 — Habit Tracker *(new feature)*
> Track daily habits, streaks, and consistency over time.

**Backend:**
- [ ] Create `backend/modules/habits.py`
- [ ] Habit model: `{ id, name, description, frequency: "daily"|"weekly", target_days: [], created_at }`
- [ ] Log model: `{ habit_id, date, completed: bool, note }`
- [ ] Storage: `backend/data/habits.json`
- [ ] API endpoints:
  - `GET /api/habits` — list all habits
  - `POST /api/habits` — create habit
  - `POST /api/habits/{id}/log` — mark done/undone for a date
  - `GET /api/habits/{id}/streak` — return current streak + longest streak
  - `GET /api/habits/summary` — today's habits + completion %
  - `DELETE /api/habits/{id}` — delete habit

**Frontend:**
- [ ] Create `frontend/src/pages/HabitsPage.jsx`
- [ ] Show today's habits as checkboxes (check off as you go)
- [ ] Streak counter per habit (🔥 7 days)
- [ ] Weekly heatmap grid (like GitHub contributions)
- [ ] Add to `App.jsx` routes and `Sidebar.jsx`

**AI Integration:**
- [ ] Add `track_habit` and `habit_summary` intents to the chat assistant
- [ ] "Did I meditate today?" → check log → reply

---

### 2.2 — Enhanced Todo (Upgrade Existing)
> Current todo is a flat list. Needs due dates, tags, and smarter views.

- [ ] Add `due_date`, `tags`, `created_at`, `updated_at` fields to todo model
- [ ] Add `GET /api/todos/due-today` endpoint
- [ ] Add `GET /api/todos/overdue` endpoint
- [ ] Add tag filtering to `GET /api/todos?tag=work`
- [ ] Update `TodoPage.jsx` to show due date badges + overdue highlighting
- [ ] Add date picker when creating/editing a todo
- [ ] Add tag input (comma-separated) to todo form
- [ ] Show "Due Today" and "Overdue" sections at the top

---

### 2.3 — Enhanced Calendar (Upgrade Existing)
> Calendar already integrates with Google Calendar (OAuth). Needs polish.

- [ ] Fix: Google OAuth currently requires a browser popup — breaks when running headless/server
  - [ ] Switch to OAuth service account or pre-generate refresh token saved in `.env`
- [ ] Add a local fallback calendar (stored in `events.json`) for when Google isn't configured
- [ ] `CalendarPage.jsx` — add week view (not just month view)
- [ ] `CalendarPage.jsx` — clicking a day opens event detail / create modal
- [ ] Add recurring events support (daily, weekly, monthly)
- [ ] Send browser push notifications for upcoming events (via Service Worker)

---

### 2.4 — Journal / Daily Log *(new feature)*
> Private daily journal with mood tracking and free-form notes.

**Backend:**
- [ ] Create `backend/modules/journal.py`
- [ ] Entry model: `{ id, date, mood: 1-5, entry: str, tags: [], created_at }`
- [ ] Storage: `backend/data/journal.json`
- [ ] API endpoints:
  - `GET /api/journal` — list entries (paginated)
  - `POST /api/journal` — create/update today's entry
  - `GET /api/journal/{date}` — get entry for a specific date
  - `GET /api/journal/stats` — mood trend over last 30 days

**Frontend:**
- [ ] Create `frontend/src/pages/JournalPage.jsx`
- [ ] Today's entry textarea (auto-saves on blur)
- [ ] Mood picker (1–5 emoji scale)
- [ ] Past entries list with mood colour coding
- [ ] Mood trend mini-chart (line chart, last 30 days)

---

### 2.5 — Dashboard / Home Screen *(new feature)*
> Currently the home screen is just the AI chat. Build a proper daily dashboard.

- [ ] Create `frontend/src/pages/DashboardPage.jsx`
- [ ] Make Dashboard the new default route (`/`)
- [ ] Move Chat to `/chat`
- [ ] Dashboard widgets:
  - [ ] 🕐 Today's date + greeting ("Good morning, Chida")
  - [ ] ✅ Habits due today (quick-check from dashboard)
  - [ ] 📋 Todos due today / overdue count
  - [ ] 📅 Next 3 calendar events
  - [ ] 💰 Finance: this month's spend vs last month
  - [ ] 📔 Mood streak / journal prompt ("How are you feeling today?")

---

## 🟢 PHASE 3 — Polish & Power Features

### 3.1 — Progressive Web App (PWA)
> Install on phone home screen, works offline, feels native.

- [ ] Add `vite-plugin-pwa` to frontend
- [ ] Create `manifest.json` with app name, icon, theme colour
- [ ] Add Service Worker for offline caching (cache static assets + last data)
- [ ] Add install prompt for mobile browsers ("Add to Home Screen")

### 3.2 — Finance Improvements
> Finance module is solid but needs UX polish and better AI categorisation.

- [ ] Fix: Ollama fallback for transaction categorisation (currently breaks if Ollama is offline)
  - [ ] Use rule-based keyword matching as primary, AI only for ambiguous ones
- [ ] Add budget goals per category (e.g. "Food budget: ₹5,000/month")
  - [ ] `POST /api/finance/budgets`
  - [ ] Show budget vs actual bar chart on Finance dashboard
- [ ] Add recurring expense detection (same merchant, similar amount each month)
- [ ] Export transactions to CSV from the UI
- [ ] Add "split" support (mark a transaction as shared, track your share)

### 3.3 — Notes Upgrade (rename from "girlfriend.py")
> The notes module (`girlfriend.py`) is a simple key-value store. Upgrade it.

- [ ] Rename `girlfriend.py` → `notes.py`, rename `GIRLFRIEND_FILE` → `NOTES_FILE`
  - Update all imports in `main.py`
- [ ] Upgrade from key-value pairs → rich notes with title, body, tags, created_at
- [ ] Add `GET /api/notes/search?q=` for full-text search
- [ ] `NotesPage.jsx` — grid view of notes cards (like Apple Notes / Notion)
- [ ] Add markdown rendering in note body
- [ ] Pin important notes to top

### 3.4 — Vault Security Upgrade
> Vault currently stores passwords in plaintext JSON. This is a security risk.

- [ ] Encrypt vault data at rest using `cryptography` (Fernet symmetric encryption)
- [ ] Master password input at startup — derive encryption key (never stored)
- [ ] Add vault lock/unlock in `VaultPage.jsx`
- [ ] Add password strength indicator when adding entries
- [ ] Add TOTP (2FA code) field support

### 3.5 — AI Chat Upgrade
> Chat assistant is powerful but limited to predefined intents. Make it smarter.

- [ ] Add chat history persistence (`backend/data/chat_history.json`)
- [ ] "What tasks do I have this week?" → query todos + calendar + return summary
- [ ] "How much did I spend this month?" → query finance module
- [ ] "What habits did I miss this week?" → query habits module
- [ ] Add voice input (Web Speech API) in `ChatPage.jsx`
- [ ] Show "thinking…" streaming indicator while AI responds

---

## ⚙️ PHASE 4 — Infrastructure & Code Quality

### 4.1 — Replace JSON Files with SQLite
> JSON files are fine for small data, but SQLite is faster, safer (concurrent writes), and easier to query.

- [ ] Add `sqlalchemy` + `aiosqlite` to `requirements.txt`
- [ ] Create `backend/core/database.py` with SQLAlchemy setup
- [ ] Migrate models: todos, habits, journal, notes, vault, finance ledger
- [ ] Write one-time migration script: `migrate_json_to_sqlite.py`
- [ ] Keep JSON as a fallback export format

### 4.2 — Proper Logging & Error Handling
- [ ] Add structured logging (JSON format) to all backend modules
- [ ] Add a `GET /api/logs` endpoint for viewing recent errors from the UI
- [ ] Wrap all Ollama/Gemini calls in proper try/except with user-friendly errors
- [ ] Add Sentry (free tier) for error tracking in production

### 4.3 — Backup & Data Export
- [ ] Add `GET /api/export` → returns a zip of all `backend/data/*.json`
- [ ] Add a "Download Backup" button in `SettingsPage.jsx`
- [ ] Add `POST /api/import` → restore from a backup zip
- [ ] Schedule auto-backup: daily zip copied to a configured folder (e.g. Google Drive)

---

## 📱 Quick Reference — Current State of the App

| Module | Backend | Frontend | AI-integrated | Status |
|---|---|---|---|---|
| Chat / AI | ✅ | ✅ | ✅ | Working — needs fallback |
| Finance | ✅ | ✅ | ✅ (Ollama) | Working — Ollama-dependent |
| Todos | ✅ | ✅ | ✅ | Working — needs due dates |
| Notes | ✅ | ✅ | ✅ | Working — needs upgrade |
| Calendar | ✅ | ✅ | ✅ | Working — Google OAuth fragile |
| Vault | ✅ | ✅ | ❌ | Working — plaintext risk |
| **Habits** | ❌ | ❌ | ❌ | **Not built yet** |
| **Journal** | ❌ | ❌ | ❌ | **Not built yet** |
| **Dashboard** | ❌ | ❌ | — | **Not built yet** |

---

*Last updated: 2026-11-19*
