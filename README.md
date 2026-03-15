# Expense Logger — LLM-Powered

A CLI tool that lets you log **and query** expenses in plain English.  
An LLM (OpenAI) extracts structured fields for logging and generates SQL for queries — all via tool-calling.

## Project Structure

```
expense_manager/
├── main.py            # CLI entry point (dual-mode: log + query)
├── intent_router.py   # OpenAI tool-calling orchestrator
├── query_engine.py    # Text-to-SQL pipeline
├── llm_extractor.py   # Expense extraction (log path)
├── db.py              # SQLite init, insert, query
├── models.py          # Pydantic Expense schema
├── config.py          # Environment variable loading
├── requirements.txt
└── README.md
```

## Setup

### 1. Navigate to the project folder

```bash
cd expense_manager
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your OpenAI API key

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...your-key-here...
```

Optional overrides:

```
DB_PATH=expenses.db       # SQLite file path (default: expenses.db)
OPENAI_MODEL=gpt-4o-mini  # model to use   (default: gpt-4o-mini)
```

## Usage

```bash
python main.py
```

The same prompt handles both logging and querying:

```
💬 You: I spent 500 on shoes today using UPI         ← logs expense
💬 You: Paid 1200 for dinner yesterday with credit card
💬 You: how much did I spend this month              ← queries DB
💬 You: show my last 5 expenses
💬 You: what is my biggest expense category
💬 You: which payment mode did I use the most
💬 You: quit
```

### Example log output

```
✅ Saved expense #1:
  {
      "amount": 500.0,
      "category": "shopping",
      "date": "2026-03-15",
      "payment_mode": "UPI",
      "description": "shoes",
      "id": 1
  }
```

### Example query output

```
🤖 You spent ₹3,200 this month across 4 expenses.
```

## How It Works

### Logging path

```
User input → intent_router (no tool called) → llm_extractor → SQLite INSERT
```

### Query path (Text-to-SQL)

```
User input → intent_router
           → OpenAI calls read_expenses tool
           → query_engine:
               1. Generate SQL  (LLM + schema + today's date)
               2. Validate SQL  (only SELECTs allowed)
               3. Execute SQL   (SQLite)
               4. Return JSON rows
           → OpenAI produces human-readable answer
```

The `intent_router` uses `tool_choice="auto"` — the model decides whether to call the tool based on context.

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

The SQLite file (`expenses.db` by default) is created automatically on first run.

## Supported Categories

`food` · `shopping` · `transport` · `entertainment` · `health` · `utilities` · `other`

## Notes

- If no date is mentioned, today's date is used.
- If no payment mode is mentioned, `cash` is used.
- The SQL pipeline rejects any non-`SELECT` statement to prevent mutations via natural language.
