"""
intent_router.py — Classifies user input as LOG, QUERY, or CHAT via OpenAI tool-calling.

Returns a tuple: (intent, payload)
  intent == "query" -> payload is the AI's natural-language answer to a spending question
  intent == "log"   -> payload is the raw user text (caller runs llm_extractor)
  intent == "chat"  -> payload is the AI's direct conversational reply
"""
import json
from datetime import date
from openai import OpenAI
from query_engine import TOOL_DEFINITION, execute_read_expenses
from config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

TODAY = date.today().isoformat()

ROUTER_SYSTEM_PROMPT = f"""You are a helpful personal expense assistant. Today is {TODAY}.

The user's message falls into exactly one of three categories:

1. LOG — The user is describing a new expense they want to record.
   Examples: "I spent 500 on shoes using UPI", "paid 200 for coffee"
   -> Reply with exactly the word: LOG

2. QUERY — The user is asking a question about their past spending/expenses in the database.
   Examples: "how much did I spend this month", "show my last 5 expenses", "what category do I spend most on"
   -> Call the read_expenses tool.

3. CHAT — Anything else: greetings, general questions, clarifications, meta questions about the conversation.
   Examples: "what was my last query", "hello", "what can you do", "what did I just say"
   -> Reply conversationally and helpfully. Do NOT call the tool. Do NOT say LOG.

Be precise about which category applies. When in doubt between LOG and CHAT, ask yourself: is there a clear monetary amount being spent? If not, it is CHAT.
"""


def route(user_input: str) -> tuple[str, str]:
    """
    Route user input to LOG, QUERY, or CHAT pipeline.

    Returns:
      ("query", answer_text)  -- AI answered a spending question using the DB
      ("log",   user_input)   -- caller should extract & insert expense
      ("chat",  answer_text)  -- AI answered a general/conversational question
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

    # ---- Tool call path: user asked about spending history ------------------
    if choice.finish_reason == "tool_calls":
        tool_call = choice.message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        query_text = args.get("query", user_input)

        # Run the Text-to-SQL pipeline
        tool_result = execute_read_expenses(query_text)

        # Second LLM call — turn raw JSON rows into a human-readable answer
        messages.append(choice.message)
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

    # ---- No tool call: check what the model replied -------------------------
    reply = choice.message.content.strip() if choice.message.content else ""

    # Strict LOG detection: only the exact word "LOG" (case-insensitive)
    if reply.strip().upper() == "LOG":
        return ("log", user_input)

    # Anything else is a direct conversational (CHAT) answer
    return ("chat", reply)
