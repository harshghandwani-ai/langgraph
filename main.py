"""
Expense Logger — main CLI entry point.

Usage:
    python main.py

Supports three modes in the same REPL:
  * Log an expense  -- "I spent 500 on shoes using UPI"
  * Query expenses  -- "how much did I spend this month"
  * General chat    -- "what was my last query", "hello"
"""
import json
import sys
from db import init_db, insert_expense
from llm_extractor import extract_expense
from intent_router import route


BANNER = """
╔══════════════════════════════════════════════════════╗
║         💸  Expense Logger  ·  AI-Powered            ║
║                                                      ║
║  Log  : "spent 500 on shoes using UPI"               ║
║  Query: "how much did I spend this month"            ║
║  Chat : "what can you do", "what was my last query"  ║
║  Exit : quit / exit / q                              ║
╚══════════════════════════════════════════════════════╝
"""


def _handle_log(user_input: str) -> None:
    """Extract and persist a new expense from natural-language text."""
    print("  ⏳ Extracting expense...")
    try:
        expense = extract_expense(user_input)
    except Exception as e:
        print(f"  ❌ Failed to extract expense: {e}\n")
        return

    try:
        row_id = insert_expense(expense)
    except Exception as e:
        print(f"  ❌ Failed to save expense: {e}\n")
        return

    result = expense.model_dump()
    result["id"] = row_id
    print(f"  ✅ Saved expense #{row_id}:")
    print("  " + json.dumps(result, indent=4).replace("\n", "\n  "))
    print()


def _handle_query(answer: str) -> None:
    """Print the AI's natural-language answer to a spending question."""
    print(f"\n  🤖 {answer}\n")


def _handle_chat(answer: str) -> None:
    """Print the AI's conversational reply."""
    print(f"\n  🤖 {answer}\n")


def main() -> None:
    init_db()
    print(BANNER)

    while True:
        try:
            user_input = input("💬 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            sys.exit(0)

        if not user_input:
            continue

        if user_input.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break

        print("  ⏳ Thinking...")
        try:
            intent, payload = route(user_input)
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
            continue

        if intent == "query":
            _handle_query(payload)
        elif intent == "chat":
            _handle_chat(payload)
        else:
            # payload is the original user text; run the log pipeline
            _handle_log(payload)


if __name__ == "__main__":
    main()