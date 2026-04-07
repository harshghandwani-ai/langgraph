import json
from langchain_core.tools import tool
from typing import Literal, Optional
from db import upsert_budget
from query_engine import execute_read_expenses
from intent_router import LogExpenseArgs

@tool
def log_expense_tool(
    amount: float,
    category: Literal["food", "shopping", "commute", "travel", "entertainment", "health", "utilities", "salary", "gift", "investment", "other"],
    date: str,
    payment_mode: str,
    description: str,
    type: str = "expense"
) -> str:
    """Extracts and formats transaction details. Call this when the user wants to log an expense or income.
    This does NOT save it directly, it brings it back to the user for confirmation."""
    preview = {
        "amount": amount,
        "category": category,
        "date": date,
        "payment_mode": payment_mode,
        "description": description,
        "type": type,
        "source": "text"
    }
    return json.dumps({"status": "preview_ready", "expense": preview})

# We'll use injected state for user_id in the Node, so the tool itself might just gather args, or we can use an approach where we handle it in executor
@tool
def set_budget_tool(
    amount: float,
    category: Literal["food", "shopping", "commute", "travel", "entertainment", "health", "utilities", "salary", "gift", "investment", "other", "total"] = "total",
    period: str = "monthly"
) -> str:
    """Sets a budget for the user."""
    # Note: user_id will be bound by the executor or we return a dict for the executor to process
    return json.dumps({"action": "set_budget", "amount": amount, "category": category, "period": period})

@tool
def read_expenses_tool(query: str) -> str:
    """Queries the database for past expenses using natural language."""
    # Note: user_id will get injected by the executor
    return json.dumps({"action": "read_expenses", "query": query})

@tool
def read_budgets_tool(
    category: Literal["food", "shopping", "commute", "travel", "entertainment", "health", "utilities", "salary", "gift", "investment", "other", "total"] = "total"
) -> str:
    """Queries the database for the user's budget(s) for a specific category or total."""
    # Note: user_id will get injected by the executor
    return json.dumps({"action": "read_budgets", "category": category})
