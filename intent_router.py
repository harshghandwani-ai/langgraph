"""
intent_router.py — Classifies user input as LOG or QUERY via OpenAI tool-calling.

Returns a tuple: (intent, payload)
  intent == "query" → payload is the AI's natural-language answer string
  intent == "log"   → payload is the raw user text (caller runs llm_extractor)
"""
from datetime import date
from openai import OpenAI
from query_engine import TOOL_DEFINITION, execute_read_expenses
from config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

TODAY = date.today().isoformat()

ROUTER_SYSTEM_PROMPT = f"""You are a personal expense assistant. Today is {TODAY}.

The user can either:
  (a) Log a new expense — e.g. "I spent 500 on shoes using UPI"
  (b) Ask a question about past expenses — e.g. "how much did I spend this month"

If the user is asking a question about their spending history, call the read_expenses tool.
If the user is describing a new expense to log, do NOT call the tool — reply with exactly:
  LOG
and nothing else.
"""


def route(user_input: str) -> tuple[str, str]:
    """
    Route user input to either the query pipeline or the log pipeline.

    Returns:
      ("query", answer_text)  — AI answered a spending question
      ("log",   user_input)   — caller should extract & insert expense
    """
    messages = [
        {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]

    # First LLM call — may or may not invoke the tool
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        tools=[TOOL_DEFINITION],
        tool_choice="auto",
        temperature=0,
    )

    choice = response.choices[0]

    # ── Tool call path: user asked a query ────────────────────────────────────
    if choice.finish_reason == "tool_calls":
        tool_call = choice.message.tool_calls[0]
        import json
        args = json.loads(tool_call.function.arguments)
        query_text = args.get("query", user_input)

        # Run the Text-to-SQL pipeline
        tool_result = execute_read_expenses(query_text)

        # Second LLM call — turn raw JSON rows into a human-readable answer
        messages.append(choice.message)          # assistant message with tool call
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": tool_result,
        })

        final_response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.3,
        )
        answer = final_response.choices[0].message.content.strip()
        return ("query", answer)

    # ── No tool call: model said LOG (or gave some other text) ───────────────
    return ("log", user_input)
