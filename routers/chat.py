"""
routers/chat.py -- Unified /api/chat endpoint.

Accepts any natural-language message and routes it to the correct pipeline:
  - log   -> LLM extracts expense fields, returns ExpensePreview (NOT saved yet)
             The frontend must call POST /api/expenses/confirm to save.
  - query -> Text-to-SQL pipeline -> returns AI answer
  - chat  -> direct LLM reply    -> returns AI answer
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import json
import time
import uuid
import logging
import asyncio

from auth_utils import TokenData, get_current_user
from db import get_chat_history, insert_chat_message, upsert_budget
from intent_router import route, client, ROUTER_SYSTEM_PROMPT
from config import OPENAI_MODEL
from query_engine import execute_read_expenses, summarize_results
from schemas import ChatRequest, ChatResponse, ExpensePreview
from db import clear_chat_history

router = APIRouter()
logger = logging.getLogger(__name__)

@router.delete("")
async def clear_chat(current_user: TokenData = Depends(get_current_user)):
    clear_chat_history(current_user.user_id)
    return {"status": "cleared"}


@router.post(
    "",
    summary="Unified streaming chat endpoint",
)
async def chat(
    body: ChatRequest,
    current_user: TokenData = Depends(get_current_user),
):
    async def event_generator():
        request_id = str(uuid.uuid4())[:8]
        t_request_start = time.time()

        # 1. Fetch history (capped at 8 messages / 4 turns)
        history = get_chat_history(current_user.user_id, limit=8)
        
        # Insert user message for context immediately
        insert_chat_message(current_user.user_id, "user", body.message)
        
        try:
            # 2. Agentic Graph Execution
            t_invoke = time.time()
            from graph.workflow import create_graph
            graph_app = create_graph()
            
            # Run the agentic loop
            state = graph_app.invoke({
                "input": body.message,
                "user_id": current_user.user_id,
                "chat_history": history,
                "past_steps": [],
                "plan": [],
                "error_count": 0
            }, config={"configurable": {"thread_id": str(current_user.user_id)}})

            logger.info(
                "[LATENCY] request_id=%s stage=graph_execution duration_ms=%d",
                request_id, round((time.time() - t_invoke) * 1000)
            )

            # Analyze state to determine frontend event type
            past_steps = state.get("past_steps", [])
            messages = state.get("messages", [])
            
            final_answer = state.get("final_response")
            if not final_answer and messages:
                final_answer = messages[-1].content
            if not final_answer:
                final_answer = "Okay, understood."

            is_log = False
            is_budget = False
            is_query = False
            query_db_res = None
            expense_preview = None

            for step_name, res_str in past_steps:
                try:
                    res_json = json.loads(res_str)
                    if res_json.get("status") == "preview_ready":
                        is_log = True
                        expense_preview = res_json.get("expense")
                    elif "db_result" in res_json:
                        is_query = True
                        query_db_res = res_json.get("db_result")
                    elif "budget" in str(res_json).lower():
                        is_budget = True
                except:
                    pass

            # Return the correct visual widget
            if is_log and expense_preview:
                yield f"data: {json.dumps({'type': 'intent', 'value': 'log'})}\n\n"
                yield f"data: {json.dumps({'type': 'log', 'answer': final_answer, 'expense': expense_preview})}\n\n"
            elif is_query:
                from query_engine import summarize_results
                yield f"data: {json.dumps({'type': 'intent', 'value': 'query'})}\n\n"
                completion = summarize_results(body.message, query_db_res, history=history)
                full_content = ""
                for chunk in completion:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_content += content
                        yield f"data: {json.dumps({'type': 'chunk', 'value': content})}\n\n"
                        await asyncio.sleep(0.01)
                final_answer = full_content
            elif is_budget:
                yield f"data: {json.dumps({'type': 'intent', 'value': 'budget'})}\n\n"
                yield f"data: {json.dumps({'type': 'budget', 'answer': final_answer})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'intent', 'value': 'chat'})}\n\n"
                # Chunk out the text manually without stripping newlines
                import re
                tokens = re.split(r'( )', final_answer)
                for token in tokens:
                    if token:
                        yield f"data: {json.dumps({'type': 'chunk', 'value': token})}\n\n"
                        await asyncio.sleep(0.01)

            insert_chat_message(current_user.user_id, "assistant", final_answer)
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

        finally:
            logger.info(
                "[LATENCY] request_id=%s stage=request_total duration_ms=%d",
                request_id, round((time.time() - t_request_start) * 1000)
            )

    return StreamingResponse(event_generator(), media_type="text/event-stream")
