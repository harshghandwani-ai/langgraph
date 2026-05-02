"""
Expense Logger — main CLI entry point.

Usage:
    python main.py

Drives the same LangGraph agentic pipeline used by the FastAPI app,
so CLI behaviour stays in sync with the web/mobile interface.
"""
import json
import sys
from db import init_db


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

# CLI uses a fixed placeholder user_id (no auth layer in the REPL)
CLI_USER_ID = 0


def main() -> None:
    init_db()
    print(BANNER)

    from graph.workflow import create_graph
    graph_app = create_graph()

    history: list[dict] = []

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
            state = graph_app.invoke(
                {
                    "input": user_input,
                    "user_id": CLI_USER_ID,
                    "chat_history": history,
                    "past_steps": [],
                    "plan": [],
                    "error_count": 0,
                },
                config={"configurable": {"thread_id": str(CLI_USER_ID)}},
            )
        except Exception as exc:
            print(f"  ❌ Error: {exc}\n")
            continue

        final_answer = state.get("final_response") or ""
        if not final_answer:
            messages = state.get("messages", [])
            final_answer = messages[-1].content if messages else "Okay, understood."

        # Surface any expense preview produced by the executor
        for _step_name, res_str in state.get("past_steps", []):
            try:
                res = json.loads(res_str)
                if res.get("status") == "preview_ready":
                    print("  📋 Expense preview:")
                    print("  " + json.dumps(res["expense"], indent=4).replace("\n", "\n  "))
            except Exception:
                pass

        print(f"\n  🤖 {final_answer}\n")

        # Keep a rolling window of 8 messages for context
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": final_answer})
        history = history[-8:]


if __name__ == "__main__":
    main()