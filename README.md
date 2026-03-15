# Expense Logger — LLM-Powered

Log and query expenses in plain English via both a **CLI** and a **REST API**.

## Project Structure

```
expense_manager/
├── app.py                # FastAPI entry point
├── routers/
│   └── expenses.py       # 3 API endpoints
├── schemas.py            # API request/response models
├── main.py               # CLI entry point (unchanged)
├── intent_router.py      # 3-way intent router (CLI)
├── query_engine.py       # Text-to-SQL pipeline
├── llm_extractor.py      # Expense extraction
├── db.py                 # SQLite init, insert, query
├── models.py             # Pydantic Expense domain model
├── config.py             # Env var loading
└── requirements.txt
```

## Setup

```bash
# 1. Activate virtual environment
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env
OPENAI_API_KEY=sk-...your-key-here...

# Optional
DB_PATH=expenses.db
OPENAI_MODEL=gpt-4o-mini
```

---

## Running the API Server

```bash
uvicorn app:app --reload
```

Interactive docs: **http://localhost:8000/docs**

---

## Running the API Client

Alternatively, use the lightweight client that talks to the server:

```bash
python client.py
```

This client uses the unified `/api/chat` endpoint, making it a thin wrapper around the server logic.

---

## Running the CLI (Direct DB Access)

```bash
python main.py
```

```
💬 You: spent 500 on shoes using UPI   ← logs
💬 You: how much did I spend this month ← queries DB
💬 You: what can you do                 ← general chat
💬 You: quit
```

## Database Schema

```sql
CREATE TABLE expenses (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    amount       REAL    NOT NULL,
    category     TEXT    NOT NULL,
    date         TEXT    NOT NULL,
    payment_mode TEXT    NOT NULL,
    description  TEXT    NOT NULL,
    created_at   TEXT    NOT NULL
);
```

## Notes

- CORS is open (`*`) for local development — restrict `allow_origins` in `app.py` before deploying.
- `POST /api/expenses/query` returns `sql` and `rows` alongside the AI answer so a UI can render a table.
- The SQL pipeline rejects any non-`SELECT` statement to prevent DB mutations via natural language.
