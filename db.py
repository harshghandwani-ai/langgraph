"""
db.py — Database abstraction layer.

Supports two backends, selected by the DATABASE_URL environment variable:
  - PostgreSQL (Neon or any Postgres)  when DATABASE_URL is set
  - SQLite                              when DATABASE_URL is NOT set (local dev)

The public API is identical in both cases:
    init_db()              -> None
    insert_expense(e)      -> int   (new row id)
    run_query(sql, params) -> list[dict]

SQL dialect differences handled internally:
  - SQLite uses  ?  placeholders and AUTOINCREMENT
  - Postgres uses %s placeholders and SERIAL / RETURNING id
"""
import sqlite3
from datetime import datetime, timezone

from models import Expense
from config import DB_PATH, DATABASE_URL


# ── Backend detection ─────────────────────────────────────────────────────────

_USE_POSTGRES = bool(DATABASE_URL)


# ── PostgreSQL helpers ────────────────────────────────────────────────────────

def _pg_conn():
    """Return a psycopg2 connection to Neon/Postgres."""
    import psycopg2
    import psycopg2.extras
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    return conn


# ── SQLite helpers ────────────────────────────────────────────────────────────

def _sqlite_conn() -> sqlite3.Connection:
    """Return a sqlite3 connection."""
    return sqlite3.connect(DB_PATH)


# ── Public API ────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create the expenses table if it doesn't exist."""
    if _USE_POSTGRES:
        conn = _pg_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS expenses (
                        id           SERIAL PRIMARY KEY,
                        amount       REAL        NOT NULL,
                        category     TEXT        NOT NULL,
                        date         TEXT        NOT NULL,
                        payment_mode TEXT        NOT NULL,
                        description  TEXT        NOT NULL,
                        created_at   TEXT        NOT NULL
                    )
                """)
            conn.commit()
        finally:
            conn.close()
    else:
        with _sqlite_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount       REAL    NOT NULL,
                    category     TEXT    NOT NULL,
                    date         TEXT    NOT NULL,
                    payment_mode TEXT    NOT NULL,
                    description  TEXT    NOT NULL,
                    created_at   TEXT    NOT NULL
                )
            """)
            conn.commit()


def insert_expense(expense: Expense) -> int:
    """Insert an Expense record and return the new row id."""
    created_at = datetime.now(timezone.utc).isoformat()

    if _USE_POSTGRES:
        conn = _pg_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO expenses (amount, category, date, payment_mode, description, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        expense.amount,
                        expense.category,
                        expense.date,
                        expense.payment_mode,
                        expense.description,
                        created_at,
                    ),
                )
                row_id = cur.fetchone()[0]
            conn.commit()
            return row_id
        finally:
            conn.close()
    else:
        with _sqlite_conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO expenses (amount, category, date, payment_mode, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    expense.amount,
                    expense.category,
                    expense.date,
                    expense.payment_mode,
                    expense.description,
                    created_at,
                ),
            )
            conn.commit()
            return cursor.lastrowid


def run_query(sql: str, params: tuple = ()) -> list[dict]:
    """Execute a SQL statement and return rows as list-of-dicts.

    Works for both SELECT (returns rows) and any other statement.
    Placeholder style is automatically adapted to the active backend.
    """
    if _USE_POSTGRES:
        import psycopg2.extras
        # Postgres uses %s placeholders; SQLite uses ?
        pg_sql = sql.replace("?", "%s")
        conn = _pg_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(pg_sql, params)
                try:
                    rows = cur.fetchall()
                    return [dict(r) for r in rows]
                except Exception:
                    return []
        finally:
            conn.close()
    else:
        with _sqlite_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
