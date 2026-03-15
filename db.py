import sqlite3
from datetime import datetime, timezone
from models import Expense
from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Create the expenses table if it doesn't exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                amount      REAL    NOT NULL,
                category    TEXT    NOT NULL,
                date        TEXT    NOT NULL,
                payment_mode TEXT   NOT NULL,
                description TEXT    NOT NULL,
                created_at  TEXT    NOT NULL
            )
        """)
        conn.commit()


def insert_expense(expense: Expense) -> int:
    """Insert an Expense record and return the new row id."""
    created_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
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


def run_query(sql: str) -> list[dict]:
    """Execute a validated SELECT statement and return rows as list-of-dicts."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
