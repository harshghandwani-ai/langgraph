"""
generate_planner_dataset.py

Generates 30 diverse planner test cases and runs each through the
current GPT-4o-mini planner to capture:
  - gold-standard plan steps
  - latency (ms)
  - expected tool calls (derived from plan text)

Output: dataset/planner_benchmark.jsonl
Each line:
{
  "id": 1,
  "query": "...",
  "category": "log|query|budget|multi_step|chat",
  "chat_history": [],          # non-empty for context-dependent queries
  "gpt_plan": ["step1", ...],
  "gpt_latency_ms": 312,
  "expected_tools": ["log_expense_tool"]   # inferred from plan
}
"""

import json
import os
import time
import logging
from datetime import date
from typing import List, Optional

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TODAY          = date.today().isoformat()
OUTPUT_PATH    = "dataset/planner_benchmark.jsonl"

# ── Planner schema (mirrors graph/nodes/planner.py) ──────────────────────────
class Plan(BaseModel):
    steps: List[str] = Field(description="A step-by-step plan to accomplish the user's request.")

PLANNER_SYSTEM_PROMPT = f"""You are PennyWise's Planner Agent. Today is {TODAY}.
Your job is to break down the user's request into a concrete plan using the available tools.
Focus ONLY on the most recent user request. Use chat history exclusively for missing context (e.g., if the user corrects a previous message). Do NOT re-plan or re-execute older, already completed requests.

If the request is a simple conversation, the plan should just be a single step: 'Respond to user contextually'.

Valid Categories:
    "food", "shopping", "commute", "travel", "entertainment", "health", "utilities", "salary", "gift", "investment", "other"

Available tools:
1. log_expense_tool: Extract transaction details to log an expense or income.
2. read_expenses_tool: Query the SQLite database for past transactions.
3. set_budget_tool: Set or update a budget.
4. read_budgets_tool: Queries the database to list the user's current budgets.

RULES:
- If you need to check if a budget was crossed/exceeded, you MUST explicitly include a step to use read_expenses_tool to fetch the spent amount.

Provide the smallest number of logical steps required."""

# ── 30 hand-crafted test queries ─────────────────────────────────────────────
# Each entry: (category, query, optional chat_history)
TEST_CASES = [
    # --- LOG (8 cases) ---
    ("log", "I spent 350 on lunch at McDonald's via UPI today", []),
    ("log", "Paid 1200 for electricity bill using net banking", []),
    ("log", "Got my salary of 75000 credited yesterday", []),
    ("log", "Bought groceries worth 850 from DMart, paid cash", []),
    ("log", "bhai 500 ka petrol dala aaj, UPI se", []),   # Hinglish
    ("log", "Spent 2500 on medicines from Apollo Pharmacy", []),
    ("log", "Received 5000 as a gift from mom", []),
    ("log", "Paid Netflix subscription 649 rupees via credit card", []),

    # --- QUERY (8 cases) ---
    ("query", "How much did I spend this month?", []),
    ("query", "Show me all my food expenses in the last 7 days", []),
    ("query", "What was my biggest expense last month?", []),
    ("query", "How much did I spend on travel this year?", []),
    ("query", "List all UPI transactions above 1000 rupees", []),
    ("query", "What is my total income vs expenses this month?", []),
    ("query", "Show me my last 5 transactions", []),
    ("query", "How much did I save last month?", []),

    # --- BUDGET (5 cases) ---
    ("budget", "Set my monthly food budget to 5000", []),
    ("budget", "Update my total monthly budget to 30000", []),
    ("budget", "Set a weekly commute budget of 800 rupees", []),
    ("budget", "Have I exceeded my shopping budget this month?", []),
    ("budget", "What are my current budgets?", []),

    # --- MULTI-STEP (6 cases) ---
    ("multi_step", "Log 800 for dinner and then show me today's total spending", []),
    ("multi_step", "Set my entertainment budget to 2000 and check if I've already exceeded it", []),
    ("multi_step", "I spent 1500 on a shirt. Also show me my shopping expenses this month", []),
    ("multi_step", "Add 200 for auto ride and tell me my commute spend this week", []),
    ("multi_step", "Log a salary of 80000 received today and show my total income this month", []),
    ("multi_step", "Set food budget to 4000 and check my food spending this month", []),

    # --- CHAT (3 cases) ---
    ("chat", "Hello! What can you help me with?", []),
    ("chat", "Thanks for tracking my expenses!", []),
    ("chat", "What's the weather like today?", []),   # off-topic — should be declined
]

# ── Tool keyword detection (simple heuristic for expected_tools field) ────────
TOOL_KEYWORDS = {
    "log_expense_tool":  ["log", "extract", "record", "add", "save", "expense", "income", "transaction"],
    "read_expenses_tool": ["read", "query", "fetch", "retrieve", "spending", "expenses", "transactions", "history", "total", "list"],
    "set_budget_tool":   ["set", "update", "create", "budget", "limit"],
    "read_budgets_tool": ["read budget", "check budget", "list budget", "current budget", "view budget", "exceeded", "remaining"],
}

def infer_tools(steps: List[str]) -> List[str]:
    steps_lower = " ".join(steps).lower()
    found = []
    for tool, keywords in TOOL_KEYWORDS.items():
        if any(kw in steps_lower for kw in keywords):
            found.append(tool)
    # deduplicate while preserving order
    seen = set()
    return [t for t in found if not (t in seen or seen.add(t))]


def build_planner_llm() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=0,
    ).with_structured_output(Plan)


def run_planner(llm, query: str, chat_history: list) -> tuple[List[str], float]:
    messages = [SystemMessage(content=PLANNER_SYSTEM_PROMPT)]
    for msg in chat_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            from langchain_core.messages import AIMessage
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=query))

    t0 = time.perf_counter()
    plan_obj: Plan = llm.invoke(messages)
    latency_ms = round((time.perf_counter() - t0) * 1000)

    return plan_obj.steps, latency_ms


def main():
    os.makedirs("dataset", exist_ok=True)

    llm = build_planner_llm()
    records = []

    logger.info(f"Running {len(TEST_CASES)} queries through {OPENAI_MODEL} planner...")
    logger.info(f"System date: {TODAY}\n")

    for idx, (category, query, history) in enumerate(TEST_CASES, start=1):
        logger.info(f"[{idx:02d}/{len(TEST_CASES)}] [{category.upper()}] {query[:70]}...")
        try:
            steps, latency = run_planner(llm, query, history)
            tools = infer_tools(steps)
            record = {
                "id": idx,
                "query": query,
                "category": category,
                "chat_history": history,
                "gpt_plan": steps,
                "gpt_latency_ms": latency,
                "expected_tools": tools,
            }
            logger.info(f"  ✓ {len(steps)} steps | {latency} ms | tools: {tools}")
            for i, s in enumerate(steps, 1):
                logger.info(f"    Step {i}: {s}")
        except Exception as exc:
            logger.error(f"  ✗ Failed: {exc}")
            record = {
                "id": idx,
                "query": query,
                "category": category,
                "chat_history": history,
                "gpt_plan": [],
                "gpt_latency_ms": -1,
                "expected_tools": [],
                "error": str(exc),
            }
        records.append(record)
        logger.info("")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # ── Summary stats ──────────────────────────────────────────────────────
    successful = [r for r in records if r["gpt_latency_ms"] > 0]
    latencies  = [r["gpt_latency_ms"] for r in successful]
    avg_lat    = round(sum(latencies) / len(latencies)) if latencies else 0
    step_counts = [len(r["gpt_plan"]) for r in successful]

    print("\n" + "="*60)
    print(f"  GPT-4o-mini Planner Baseline  |  {TODAY}")
    print("="*60)
    print(f"  Total queries     : {len(TEST_CASES)}")
    print(f"  Successful        : {len(successful)}")
    print(f"  Avg latency       : {avg_lat} ms")
    print(f"  Min / Max latency : {min(latencies)} ms / {max(latencies)} ms")
    print(f"  Avg plan steps    : {round(sum(step_counts)/len(step_counts), 1)}")
    print(f"\n  Dataset saved to  : {OUTPUT_PATH}")
    print("="*60)


if __name__ == "__main__":
    main()
