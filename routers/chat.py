"""
routers/chat.py -- Unified /api/chat endpoint.

Accepts any natural-language message and routes it to the correct pipeline:
  - log   -> LLM extracts expense fields, returns ExpensePreview (NOT saved yet)
             The frontend must call POST /api/expenses/confirm to save.
  - query -> Text-to-SQL pipeline -> returns AI answer
  - chat  -> direct LLM reply    -> returns AI answer
"""
from fastapi import APIRouter, HTTPException

from intent_router import route
from query_engine import execute_read_expenses, summarize_results
from schemas import ChatRequest, ChatResponse, ExpensePreview

router = APIRouter()


@router.post(
    "",
    response_model=ChatResponse,
    summary="Unified chat endpoint",
    description=(
        "Send any natural-language message. The server routes it to "
        "log an expense (returns preview for confirmation), "
        "query spending history, or answer general questions."
    ),
)
async def chat(body: ChatRequest) -> ChatResponse:
    try:
        intent, payload = route(body.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Intent routing failed: {exc}") from exc

    # ---- LOG: extract fields, return preview -- do NOT save to DB -----------
    if intent == "log":
        try:
            preview = ExpensePreview(
                amount=payload["amount"],
                category=payload["category"],
                date=payload["date"],
                payment_mode=payload["payment_mode"],
                description=payload["description"],
                ocr_text=None,
                source="text",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Could not build expense preview from extracted data: {exc}",
            ) from exc

        answer = (
            f"Here's what I extracted from your message. "
            f"Please review the details below and confirm (or edit) before saving."
        )
        return ChatResponse(intent="log", answer=answer, expense=preview)

    # ---- QUERY --------------------------------------------------------------
    if intent == "query":
        try:
            tool_result = execute_read_expenses(payload)
            answer = summarize_results(body.message, tool_result)
            return ChatResponse(intent="query", answer=answer, expense=None)
        except Exception as exc:
            raise HTTPException(
                status_code=500, detail=f"Failed to query expenses: {exc}"
            ) from exc

    # ---- CHAT ---------------------------------------------------------------
    return ChatResponse(intent=intent, answer=payload, expense=None)
