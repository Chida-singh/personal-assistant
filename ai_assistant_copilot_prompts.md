# 🧠 Local Desktop AI Assistant — Complete Copilot Prompt Guide
# All 20 prompts in order. Paste one at a time into Copilot Chat.

---

## PROMPT 1 — Project Scaffold

```
Create a Python project with the following folder structure:

assistant/
  main.py
  requirements.txt
  data/
    todos.json
    girlfriend.json
    chat_history.json
  gui/
    __init__.py
    main_window.py
    sidebar.py
    chat_bubble.py
    settings_panel.py
    tabs/
      __init__.py
      chat_tab.py
      todo_tab.py
      girlfriend_tab.py
      whatsapp_tab.py
      settings_tab.py
  core/
    __init__.py
    llm.py¦
    router.py
    storage.py
    voice.py
  modules/
    __init__.py
    calendar.py
    finance.py
    automation.py

Rules:
- Add an empty __init__.py to every package folder
- Add a one-line comment in each file describing its purpose
- Create the data/ folder with empty JSON files: todos.json, girlfriend.json, chat_history.json
  - Each file should contain an empty list: []
- Do not write any logic yet
```

---

## PROMPT 2 — Requirements File

```
Create a requirements.txt for a PySide6 desktop app with these dependencies:

- PySide6          → GUI framework
- requests         → HTTP calls to Ollama API
- pandas           → CSV parsing for finance module
- matplotlib       → Spending category bar chart
- pyautogui        → Typing automation
- pyperclip        → Copy to clipboard
- faster-whisper   → Local speech-to-text using Whisper model
- sounddevice      → Microphone audio recording
- numpy            → Audio array handling

Pin no versions. One package per line.
```

---

## PROMPT 3 — Persistent Storage Helper

```
In core/storage.py, build a simple JSON read/write helper used across all tabs.

Functions:

1. load(filename: str) -> list
   - Read data/filename.json
   - Return parsed list
   - If file is missing or invalid JSON, return []

2. save(filename: str, data: list) -> None
   - Write data to data/filename.json
   - Pretty print with indent=2

Constants (define at top):
  TODOS_FILE     = "todos.json"
  GIRLFRIEND_FILE = "girlfriend.json"
  CHAT_FILE      = "chat_history.json"

Add inline comments explaining each function.
```

---

## PROMPT 4 — LLM Module (Ollama + Streaming + QThread)

```
In core/llm.py, build the Ollama LLM integration.

Requirements:
- Base URL: configurable, default http://localhost:11434/api/chat
- Model: configurable, default "llama3"
- Maintain conversation history as a list of {role, content} dicts
- Expose: send_message(user_input, model="llama3") -> str

System prompt:
  "You are an assistant that converts user commands into JSON.
   Only return valid JSON. Do not explain. Do not add extra text.

   Supported intents:
   - check_calendar    → parameters: date
   - create_event      → parameters: title, datetime
   - analyze_statement → parameters: file_path
   - type_text         → parameters: text
   - add_todo          → parameters: task
   - complete_todo     → parameters: task
   - delete_todo       → parameters: task
   - remember          → parameters: key, value
   - recall            → parameters: key
   - general_chat      → parameters: message

   If input is conversational, return:
   { \"intent\": \"general_chat\", \"parameters\": { \"message\": \"...\" } }"

Streaming:
- Use streaming=True in the Ollama POST request
- Read chunks line by line, accumulate full response string
- Return the full string when done

QThread Worker class: LLMWorker(QThread)
- Signals: response_ready(str), error_occurred(str)
- Constructor args: user_input (str), model (str), history (list)
- run():
    1. Build payload with system prompt + history + new user message
    2. POST to Ollama with stream=True
    3. Accumulate streamed chunks
    4. Emit response_ready(full_response)
    5. On any exception → emit error_occurred("LLM unavailable.")

Add inline comments.
```

---

## PROMPT 5 — Intent Router

```
In core/router.py, build a router that reads LLM JSON output and calls the right module.

Function: route(llm_output: str, file_path: str = None) -> str

Steps:
1. Try to parse llm_output as JSON
2. Read the "intent" field
3. Dispatch to the correct function using this mapping:

   check_calendar    → modules/calendar.py :: check_events(date)
   create_event      → modules/calendar.py :: create_event(title, datetime)
   analyze_statement → modules/finance.py  :: analyze(file_path)
   type_text         → modules/automation.py :: type_text(text)
   add_todo          → modules/todo.py :: add_todo(task)
   complete_todo     → modules/todo.py :: complete_todo(task)
   delete_todo       → modules/todo.py :: delete_todo(task)
   remember          → modules/girlfriend.py :: remember(key, value)
   recall            → modules/girlfriend.py :: recall(key)
   general_chat      → return the "message" parameter directly

4. Return the result string

Fallback:
- Invalid JSON → treat as general_chat, echo the raw input
- Unknown intent → return "I'm not sure how to help with that."

Add inline comments.
```

---

## PROMPT 6 — Calendar Module

```
In modules/calendar.py, implement two stub functions using mock data. This is using google calendar. 
https://developers.google.com/workspace/calendar/api/v3/reference : fetch this for information.

1. check_events(date: str) -> str
   - Return: "You have 2 events on {date}: Team standup at 9am, Lunch at 1pm."

2. create_event(title: str, datetime: str) -> str
   - Return: "Event '{title}' added on {datetime}."

# TODO: Replace with Google Calendar API later
```

---

## PROMPT 7 — Finance Module

```
In modules/finance.py, implement a CSV bank statement analyzer.

Function: analyze(file_path: str) -> str

Steps:
1. Load CSV with pandas (expected columns: Date, Description, Amount, Category)
2. If Category column is missing, infer using keyword rules:
   - "food" / "restaurant" / "swiggy" / "zomato" → "Food"
   - "uber" / "ola" / "fuel"                      → "Transport"
   - "amazon" / "flipkart" / "shop"               → "Shopping"
   - Default                                       → "Other"
3. Group by Category, sum Amount column
4. Format as a readable summary string
5. Generate a matplotlib bar chart → save as chart.png in project root
6. Return summary text + "Chart saved as chart.png"
7. Ask for information before sorting or placing them into groups. Most of them will have a labell hopefully. 

Error handling:
- File not found → "Could not open file: {file_path}"
- Wrong columns  → "CSV format not recognized. Expected: Date, Description, Amount"
```

---

## PROMPT 8 — Todo Module

```
In modules/todo.py, implement a todo list manager using core/storage.py.

Functions:

1. add_todo(task: str) -> str
   - Load todos from storage
   - Append { "task": task, "done": false }
   - Save back
   - Return: "Added to your list: {task}"

2. complete_todo(task: str) -> str
   - Load todos
   - Find item where task name matches (case-insensitive)
   - Set "done": true
   - Save back
   - Return: "Marked as done: {task}"

3. delete_todo(task: str) -> str
   - Load todos
   - Remove item where task name matches
   - Save back
   - Return: "Deleted: {task}"

4. get_all() -> list
   - Return full list from storage

Use core/storage.py load() and save() functions.
Add inline comments.
```

---

## PROMPT 9 — Girlfriend Module

```
In modules/girlfriend.py, implement a personal notes module using core/storage.py.

Purpose: Store and recall personal notes about the user's girlfriend.
Examples: birthday, food preferences, anniversaries, pet names, dislikes, and things to do together. or stuff to remember.
give the user suggestions on what to do as well.

Functions:

1. remember(key: str, value: str) -> str
   - Load notes from storage
   - Save or update { "key": key, "value": value }
   - Return: "Got it! I'll remember that {key} is {value}."

2. recall(key: str) -> str
   - Load notes from storage
   - Find item where key matches (case-insensitive)
   - Return: "You told me {key} is {value}."
   - If not found → "I don't have anything saved for '{key}' yet."

3. get_all() -> list
   - Return full notes list from storage

Use core/storage.py load() and save() with GIRLFRIEND_FILE constant.
Add inline comments.
```

---

## PROMPT 10 — Automation Module

```
In modules/automation.py, implement the text typing function.

Function: type_text(text: str) -> str

Steps:
1. import time, pyautogui
2. Wait 2 seconds: time.sleep(2)
   # Gives user time to click into WhatsApp or any text field
3. pyautogui.typewrite(text, interval=0.03)
4. Return: "Typed successfully. ({len(text)} characters)"

Error handling:
- On any exception → return "Typing failed. Make sure a text field is focused."

# Safety note: This types at wherever the cursor is currently focused.
```

---

## PROMPT 11 — Voice Module (faster-whisper)

```
In core/voice.py, implement local speech-to-text using faster-whisper and sounddevice.

Requirements:
- Record audio from microphone for a fixed duration
- Transcribe using faster-whisper (model size: "small")
- Return transcribed text as a plain string
- Everything runs locally — no internet needed

Class: VoiceRecorder

__init__():
  - Load faster-whisper WhisperModel("small", device="cpu", compute_type="int8")
  - Set sample_rate = 16000
  - Set duration = 5  # seconds to record

record_and_transcribe() -> str:
  1. Print "Listening..." to console
  2. Use sounddevice.rec() to record audio as numpy array
  3. Use sounddevice.wait() to wait until recording is done
  4. Save audio to a temp WAV file using scipy.io.wavfile or write manually
  5. Pass WAV file to self.model.transcribe()
  6. Join all segment texts and return as a single string
  7. On any error → return ""

Add to requirements.txt: scipy

Add inline comments explaining each step.
```

---

## PROMPT 12 — Chat Bubble Widget

```
In gui/chat_bubble.py, create a custom PySide6 widget for a single chat message.

Class: ChatBubble(QWidget)

Constructor args:
- message: str
- sender: str  → "user" or "assistant"

Visual rules (dark theme):
- User bubble:
    align: right
    background: #2563EB
    text color: #FFFFFF
    border-radius: 18px 18px 4px 18px

- Assistant bubble:
    align: left
    background: #1E293B
    text color: #CBD5E1
    border-radius: 18px 18px 18px 4px

- Padding: 10px 16px
- Font: "Consolas", size 13px
- Max width: 70% of window
- Word wrap: enabled

Use QLabel + QHBoxLayout + Qt stylesheets only.
No external libraries.
```

---

## PROMPT 13 — Sidebar Navigation

```
In gui/sidebar.py, create a left sidebar navigation widget.

Class: Sidebar(QWidget)

Fixed width: 200px
Background: #0A0F1E

Navigation buttons (top to bottom):
  💬  Chat
  ✅  Todo
  💕  Girlfriend
  🎙️  Voice Reply
  ⚙   Settings

Each button:
- Full width
- Height: 48px
- Font: "Segoe UI", 13px
- Default style: background transparent, text #94A3B8
- Active/selected style: background #1E293B, text #F1F5F9, left border 3px solid #2563EB
- Hover style: background #1E293B

Signal: tab_changed(str)
- Emits the tab name as a string when a button is clicked
- Example: "chat", "todo", "girlfriend", "voice", "settings"

Add inline comments.
```

---

## PROMPT 14 — Chat Tab

```
In gui/tabs/chat_tab.py, build the main chat interface tab.

Class: ChatTab(QWidget)

Layout (top to bottom):
1. Scrollable chat area
   - QScrollArea with QVBoxLayout inside
   - Renders ChatBubble widgets
   - Auto-scrolls to bottom on new message
   - Load previous messages from core/storage.py CHAT_FILE on startup

2. "Thinking..." indicator
   - A small label that shows while LLM is processing
   - Hidden by default, shown during LLM call

3. Bottom input bar (horizontal):
   - QLineEdit → placeholder: "Ask me anything..."
   - "Send" button
   - "🎤" mic button → triggers voice recording

Behavior:
- On Send:
    1. Read input text
    2. Add user ChatBubble
    3. Clear input box
    4. Show "Thinking..." label
    5. Start LLMWorker (QThread) with the message
    6. On response_ready → call router.route() → add assistant ChatBubble
    7. Hide "Thinking..." label
    8. Save updated conversation to storage

- On Mic button:
    1. Disable mic button, change label to "🔴 Listening..."
    2. Run VoiceRecorder.record_and_transcribe() in a QThread
    3. On result → put transcribed text into the input box
    4. Re-enable mic button, restore label to "🎤"

Dark theme:
  background: #0F172A
  input: #1E293B, border: #334155, text: #F1F5F9
  Send button: #2563EB

Add inline comments.
```

---

## PROMPT 15 — Todo Tab

```
In gui/tabs/todo_tab.py, build the todo list tab.

Class: TodoTab(QWidget)

Layout (top to bottom):
1. Title label: "✅ My Tasks"
   - Font: "Segoe UI", 18px bold, color #F1F5F9

2. Input row (horizontal):
   - QLineEdit → placeholder: "Add a new task..."
   - "Add" button → calls add_task()

3. Task list area (QScrollArea):
   - For each task in storage, render a TaskRow widget

TaskRow widget (one per task):
- Horizontal layout:
  - Checkbox (QCheckBox) → on check, call complete_todo(task)
  - Task label (QLabel) → strikethrough style if done
  - Delete button ("🗑") → calls delete_todo(task)
- Background: #1E293B, border-radius: 8px, padding: 8px
- Done tasks: text color #475569, strikethrough

Functions:
- load_tasks() → read from storage, render TaskRow for each item
- add_task()   → call modules/todo.py add_todo(), reload list
- refresh()    → clear and re-render all task rows

Load tasks on tab open.
Dark theme consistent with rest of app.
Add inline comments.
```

---

## PROMPT 16 — Girlfriend Tab

```
In gui/tabs/girlfriend_tab.py, build the personal notes tab.

Class: GirlfriendTab(QWidget)

Layout:
1. Title: "💕 About Her"
   - Font: "Segoe UI", 18px bold, color #F472B6

2. Input form (two QLineEdit fields side by side):
   - Key field   → placeholder: "e.g. birthday, favourite food"
   - Value field → placeholder: "e.g. March 5, Pasta"
   - "Save" button → calls remember(key, value), reloads notes

3. Ask section:
   - QLineEdit → placeholder: "Ask something... e.g. What does she like?"
   - "Ask" button → sends to LLM as a general_chat with context from stored notes
   - Response shown in a QLabel below

4. Notes list (QScrollArea):
   - Display all saved notes as rows
   - Each row: key (bold, #F472B6) → value (#CBD5E1) — Delete button

Functions:
- load_notes()    → read from storage, render rows
- save_note()     → call modules/girlfriend.py remember(), reload
- delete_note(key) → remove from storage, reload
- ask_question()  → build prompt: "Based on these notes: {notes}, answer: {question}"
                     send to LLM, display response

Dark theme:
  background: #0F172A
  card background: #1E293B
  accent: #F472B6

Add inline comments.
```

---

## PROMPT 17 — Voice Reply Tab

```
In gui/tabs/whatsapp_tab.py, build the voice reply tab.

Class: VoiceReplyTab(QWidget)

Purpose:
  User presses mic → speaks → transcribed text appears → 
  one click copies it → user pastes it anywhere (WhatsApp, DMs, email)

Layout (top to bottom):
1. Title: "🎙️ Voice Reply"
   Font: "Segoe UI", 18px bold, color #F1F5F9

2. Instructions label:
   "Press the mic, speak your message, then copy and paste anywhere."
   Color: #94A3B8, size 12px

3. Big mic button (center):
   - "🎤 Hold to Speak" button
   - Large: 120x120px, circular, background #2563EB
   - On click → starts recording
   - While recording → changes to "🔴 Listening..." red background
   - After done → restores to original

4. Transcription box:
   - QTextEdit (read-only)
   - Shows transcribed text after recording
   - Placeholder: "Your words will appear here..."
   - Background: #1E293B, text: #F1F5F9

5. Action buttons row:
   - "📋 Copy to Clipboard" → copies transcription text using pyperclip
   - "⌨️ Auto-Type" → calls modules/automation.py type_text() with transcription
   - "🗑 Clear" → clears the transcription box

Recording flow:
1. On mic button click → disable button, label "🔴 Listening..."
2. Run VoiceRecorder.record_and_transcribe() in a QThread
3. On result → fill transcription box
4. Re-enable mic button

Add inline comments.
```

---

## PROMPT 18 — Settings Tab

```
In gui/tabs/settings_tab.py, build the settings tab.

Class: SettingsTab(QWidget)

Layout (top to bottom):
1. Title: "⚙ Settings"
   Font: "Segoe UI", 18px bold, color #F1F5F9

2. Section: LLM Settings
   - Label: "Ollama Model"
   - QComboBox: llama3, mistral, gemma, phi3  (default: llama3)
   - Label: "Ollama Base URL"
   - QLineEdit: default http://localhost:11434
   - "Save Settings" button → updates llm.py config at runtime, shows confirmation

3. Section: Voice Settings
   - Label: "Recording Duration (seconds)"
   - QSpinBox: min 3, max 15, default 5
   - Updates VoiceRecorder.duration at runtime

4. Section: Data Management
   - "🗑 Clear Chat History" button → clears data/chat_history.json, shows confirmation
   - "🗑 Clear Todo List" button   → clears data/todos.json, shows confirmation
   - "🗑 Clear Girlfriend Notes"   → clears data/girlfriend.json, shows confirmation

5. Section: Export
   - "💾 Export Chat" button → saves chat history as chat_export.txt in project root
   - Shows QMessageBox: "Chat exported to chat_export.txt"

All confirmation dialogs use QMessageBox.
Dark theme consistent with rest of app.
Add inline comments.
```

---

## PROMPT 19 — Main Window

```
In gui/main_window.py, build the main application window.

Class: MainWindow(QMainWindow)

Layout:
- Window title: "🧠 Local AI Assistant"
- Minimum size: 1000 x 650
- Background: #0F172A

Two-panel horizontal layout:
  Left:  Sidebar widget (fixed 200px)
  Right: QStackedWidget containing all 5 tabs

Tabs in QStackedWidget (must match sidebar order):
  Index 0 → ChatTab
  Index 1 → TodoTab
  Index 2 → GirlfriendTab
  Index 3 → VoiceReplyTab
  Index 4 → SettingsTab

Sidebar connection:
- Connect Sidebar.tab_changed signal to a slot: switch_tab(name: str)
- switch_tab maps name to index and calls stacked_widget.setCurrentIndex()

Tab name → index map:
  "chat"       → 0
  "todo"       → 1
  "girlfriend" → 2
  "voice"      → 3
  "settings"   → 4

Default tab on launch: "chat" (index 0)

Apply global dark stylesheet to MainWindow:
  QMainWindow  { background: #0F172A; color: #F1F5F9; }
  QLineEdit    { background: #1E293B; border: 1px solid #334155;
                 border-radius: 8px; color: #F1F5F9; padding: 6px 10px; }
  QPushButton  { background: #2563EB; color: #FFFFFF; border-radius: 8px;
                 padding: 8px 16px; font-size: 13px; }
  QPushButton:hover { background: #1D4ED8; }
  QScrollArea  { border: none; background: transparent; }

Add inline comments.
```

---

## PROMPT 20 — Main Entry Point

```
In main.py, write the application entry point.

Steps:
1. Import sys, QApplication from PySide6.QtWidgets
2. Import MainWindow from gui/main_window
3. Add comment block at top:
   # ============================================
   # Local AI Assistant
   # Run:     python main.py
   # Requires: Ollama running → ollama serve
   #           Model pulled  → ollama pull llama3
   # Install:  pip install -r requirements.txt
   # ============================================
4. if __name__ == "__main__":
5. app = QApplication(sys.argv)
6. app.setApplicationName("Local AI Assistant")
7. Apply dark QPalette:
   - Window:          #0F172A
   - WindowText:      #F1F5F9
   - Base:            #1E293B
   - AlternateBase:   #0F172A
   - Text:            #F1F5F9
   - Button:          #1E293B
   - ButtonText:      #F1F5F9
   - Highlight:       #2563EB
   - HighlightedText: #FFFFFF
8. window = MainWindow()
9. window.show()
10. sys.exit(app.exec())
```

---

## PROMPT 21 — Final Integration Check

```
Review all files in the assistant/ project and verify:

1.  main.py launches MainWindow correctly with dark QPalette
2.  Sidebar.tab_changed signal is connected to MainWindow.switch_tab()
3.  QStackedWidget switches tabs correctly for all 5 tabs
4.  ChatTab uses LLMWorker (QThread) — no blocking on main thread
5.  LLMWorker response_ready → router.route() → ChatBubble added
6.  Chat history is saved to data/chat_history.json after each message
7.  Chat history is loaded from storage on ChatTab startup
8.  TodoTab loads from data/todos.json and saves on every add/complete/delete
9.  GirlfriendTab loads from data/girlfriend.json and saves on every change
10. VoiceReplyTab mic button runs VoiceRecorder in a QThread (non-blocking)
11. VoiceRecorder transcription fills the text box correctly
12. Auto-Type button calls automation.type_text() with the transcribed text
13. Copy button uses pyperclip to copy transcription to clipboard
14. SettingsTab saves model + URL and updates llm.py config at runtime
15. SettingsTab clear buttons wipe the correct JSON files
16. Chat export writes formatted messages to chat_export.txt
17. Finance module generates chart.png correctly
18. All modules return user-friendly strings on error
19. Dark theme is consistent across all tabs and widgets
20. requirements.txt includes all packages (add scipy if missing)

Fix any missing imports, disconnected signals, or broken references.
Do not change the folder structure.
```

---

## ✅ Setup & Run Instructions

```bash
# Step 1 — Install all dependencies
pip install -r requirements.txt

# Step 2 — Pull the LLM model (first time only, ~4.7GB)
ollama pull llama3

# Step 3 — Start Ollama in the background
ollama serve

# Step 4 — Launch the app
python main.py
```

---

## 📁 Final Project Structure

```
assistant/
├── main.py
├── requirements.txt
├── chart.png                  ← auto-generated by finance module
├── chat_export.txt            ← auto-generated on export
├── data/
│   ├── todos.json
│   ├── girlfriend.json
│   └── chat_history.json
├── gui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── sidebar.py
│   ├── chat_bubble.py
│   ├── settings_panel.py
│   └── tabs/
│       ├── __init__.py
│       ├── chat_tab.py
│       ├── todo_tab.py
│       ├── girlfriend_tab.py
│       ├── whatsapp_tab.py
│       └── settings_tab.py
├── core/
│   ├── __init__.py
│   ├── llm.py
│   ├── router.py
│   ├── storage.py
│   └── voice.py
└── modules/
    ├── __init__.py
    ├── calendar.py
    ├── finance.py
    ├── automation.py
    ├── todo.py
    └── girlfriend.py
```

---

*Paste prompts 1 → 21 into Copilot Chat in order. Each prompt is fully self-contained.*
*Run Prompt 21 last — it acts as a full integration review and fixes any broken wiring.*
