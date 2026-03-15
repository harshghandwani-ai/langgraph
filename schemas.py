"""
schemas.py — API-level Pydantic models for request and response shapes.

Includes ChatRequest/ChatResponse for the unified /api/chat endpoint.

Kept separate from models.py (domain Expense) for clean layering.
"""
from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Request models ────────────────────────────────────────────────────────────

class LogRequest(BaseModel):
    text: str = Field(
        ...,
        description="Natural-language expense description.",
        examples=["I spent 500 on shoes today using UPI"],
    )


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        description="Natural-language question about past expenses.",
        examples=["How much did I spend this month?"],
    )


# ── Response models ───────────────────────────────────────────────────────────

class LogResponse(BaseModel):
    id: int
    amount: float
    category: str
    date: str
    payment_mode: str
    description: str
    created_at: str


class QueryResponse(BaseModel):
    answer: str = Field(..., description="AI-generated natural-language answer.")
    sql: str = Field(..., description="The SQL query that was executed.")
    rows: list[dict[str, Any]] = Field(..., description="Raw result rows from the database.")


class ExpenseRecord(BaseModel):
    id: int
    amount: float
    category: str
    date: str
    payment_mode: str
    description: str
    created_at: str


# ── Chat (unified intent) models ──────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        description="Any natural-language input: log an expense, query history, or general chat.",
        examples=["I spent 350 on lunch", "how much did I spend today", "what can you do"],
    )


class ChatResponse(BaseModel):
    intent: str = Field(..., description="Detected intent: 'log', 'query', or 'chat'.")
    answer: str = Field(..., description="AI natural-language reply.")
    expense: Optional[LogResponse] = Field(None, description="Populated only when intent=='log'.")

