"""
query_engine.py — Text-to-SQL pipeline for expense queries.

Pipeline:
  1. Generate SQL  (LLM)
  2. Validate SQL  (only SELECTs allowed)
  3. Execute SQL   (SQLite via db.run_query)
  4. Return result (list of dicts or scalar string)
"""
import json
from datetime import date
from openai import OpenAI
from db import run_query
from config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

TODAY = date.today().isoformat()

# ─── OpenAI tool definition ───────────────────────────────────────────────────

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "read_expenses",
        "description": (
            "Query the local expenses SQLite database. "
            "Use this whenever the user asks about their spending, "
            "totals, categories, payment modes, or history."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The user's natural-language question about their expenses.",
                }
            },
            "required": ["query"],
        },
    },
}

# ─── DB schema injected into the prompt ───────────────────────────────────────

DB_SCHEMA = """
Table: expenses
  id           INTEGER PRIMARY KEY
  amount       REAL      -- monetary amount
  category     TEXT      -- food, shopping, transport, entertainment, health, utilities, other
  date         TEXT      -- YYYY-MM-DD
  payment_mode TEXT      -- cash, UPI, credit card, debit card
  description  TEXT      -- what was bought
  created_at   TEXT      -- ISO-8601 UTC timestamp
"""

SQL_SYSTEM_PROMPT = f"""You are a SQLite expert. Today is {TODAY}.

Given a natural-language question about expenses, generate a single valid SQLite SELECT statement.

Database schema:
{DB_SCHEMA}

Rules:
- Output ONLY the raw SQL. No markdown fences, no explanation.
- Use only SELECT statements.
- For date ranges use ISO-8601 strings (e.g. '{TODAY[:7]}-01' for start of current month).
- For "this week" use date('{TODAY}','-6 days') as the lower bound.
- Aliases make column names readable (e.g. SUM(amount) AS total).
- LIMIT results to 50 rows unless the user asks for more.
"""


# ─── Pipeline steps ───────────────────────────────────────────────────────────

def _generate_sql(query_text: str) -> str:
    """Step 1 — ask the LLM to produce a SELECT statement."""
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SQL_SYSTEM_PROMPT},
            {"role": "user", "content": query_text},
        ],
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def _validate_sql(sql: str) -> str:
    """Step 2 — reject anything that isn't a SELECT (safety guard)."""
    normalised = sql.lstrip().upper()
    if not normalised.startswith("SELECT"):
        raise ValueError(
            f"Only SELECT statements are allowed. Got: {sql[:80]!r}"
        )
    return sql


def _execute_sql(sql: str) -> list[dict]:
    """Step 3 — run the query and return rows as list-of-dicts."""
    return run_query(sql)


def _format_result(rows: list[dict]) -> str:
    """Step 4 — serialise to JSON string for the tool-result message."""
    if not rows:
        return json.dumps({"result": "No matching expenses found."})
    return json.dumps({"rows": rows}, default=str)


# ─── Public dispatcher ────────────────────────────────────────────────────────

def execute_read_expenses(query_text: str) -> str:
    """
    Full Text-to-SQL pipeline.
    Returns a JSON string that is sent back to the LLM as the tool result.
    """
    sql = _generate_sql(query_text)
    sql = _validate_sql(sql)
    rows = _execute_sql(sql)
    return _format_result(rows)


def summarize_results(user_input: str, tool_result: str) -> str:
    """
    Takes the raw JSON rows string from execute_read_expenses and the original user query,
    and returns a conversational natural-language answer.
    """
    system_prompt = (
        "You are a helpful personal finance assistant. "
        "Answer the user's question based strictly on the provided database results. "
        "Amount is in ₹"
    )
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User question: {user_input}\n\nDatabase results:\n{tool_result}"}
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()
