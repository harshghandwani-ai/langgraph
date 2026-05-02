"""
benchmark_planner.py

Benchmarks a model's Planner Agent against the GPT-4o-mini gold standard
stored in dataset/planner_benchmark.jsonl.

Usage:
    # Benchmark GPT-4o-mini (self-check):
    python benchmark_planner.py --model gpt-4o-mini

    # Benchmark Llama 3.1 8B via Groq:
    python benchmark_planner.py --model llama-3.1-8b-instant --provider groq

    # Benchmark a local Ollama model:
    python benchmark_planner.py --model llama3.1:8b --provider ollama

Scoring per query:
  - step_count_match   (1 pt)  : same number of steps as gold standard
  - tool_coverage      (0–1)   : fraction of expected tools mentioned in the plan
  - no_hallucination   (1 pt)  : plan only references valid tools
  - valid_json         (1 pt)  : model produced a parseable structured Plan
  Total score = average of all metrics across 30 queries (0–100%)

Results are printed as a table and saved to:
    dataset/planner_benchmark_results_<model>.json
"""

import argparse
import json
import os
import re
import time
import logging
from datetime import date
from typing import List, Optional

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

TODAY         = date.today().isoformat()
DATASET_PATH  = "dataset/planner_benchmark.jsonl"
VALID_TOOLS   = {
    "log_expense_tool",
    "read_expenses_tool",
    "set_budget_tool",
    "read_budgets_tool",
}

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


# ── Schema ────────────────────────────────────────────────────────────────────
class Plan(BaseModel):
    steps: List[str] = Field(description="A step-by-step plan to accomplish the user's request.")


# ── LLM factory ──────────────────────────────────────────────────────────────
def build_llm(model: str, provider: str) -> ChatOpenAI:
    if provider == "openai":
        return ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=model,
            temperature=0,
        ).with_structured_output(Plan)

    elif provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            api_key=os.getenv("GROQ_API_KEY", ""),
            model=model,
            temperature=0,
        ).with_structured_output(Plan)

    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=model,
            temperature=0,
        ).with_structured_output(Plan)

    else:
        raise ValueError(f"Unknown provider '{provider}'. Use: openai | groq | ollama")


# ── Inference ─────────────────────────────────────────────────────────────────
def run_planner(llm, query: str, chat_history: list) -> tuple[List[str], float, bool]:
    """Returns (steps, latency_ms, valid_json)."""
    messages = [SystemMessage(content=PLANNER_SYSTEM_PROMPT)]
    for msg in chat_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=query))

    t0 = time.perf_counter()
    try:
        plan_obj: Plan = llm.invoke(messages)
        latency_ms = round((time.perf_counter() - t0) * 1000)
        return plan_obj.steps, latency_ms, True
    except Exception as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000)
        logger.warning(f"    Structured output failed: {exc}")
        return [], latency_ms, False


# ── Scoring ───────────────────────────────────────────────────────────────────
TOOL_KEYWORDS_MAP = {
    "log_expense_tool":   ["log_expense", "log expense", "log_expense_tool"],
    "read_expenses_tool": ["read_expenses", "read expenses", "read_expenses_tool"],
    "set_budget_tool":    ["set_budget", "set budget", "set_budget_tool"],
    "read_budgets_tool":  ["read_budgets", "read budgets", "read_budgets_tool"],
}

def mentions_tool(steps: List[str], tool: str) -> bool:
    text = " ".join(steps).lower()
    return any(kw in text for kw in TOOL_KEYWORDS_MAP.get(tool, [tool.lower()]))

def score_result(gold: dict, pred_steps: List[str], valid_json: bool) -> dict:
    gold_steps = gold["gpt_plan"]
    expected_tools = gold["expected_tools"]

    # 1. Valid structured output
    score_valid = 1 if valid_json else 0

    # 2. Step count match (within ±1 is acceptable)
    gold_n = len(gold_steps)
    pred_n = len(pred_steps)
    score_step = 1 if abs(pred_n - gold_n) <= 1 else 0

    # 3. Tool coverage: fraction of expected tools that appear in plan
    if expected_tools:
        covered = sum(1 for t in expected_tools if mentions_tool(pred_steps, t))
        score_tools = covered / len(expected_tools)
    else:
        # chat / conversational — no tools expected, check plan doesn't call tools
        score_tools = 1.0 if not any(
            mentions_tool(pred_steps, t) for t in VALID_TOOLS
        ) else 0.0

    # 4. No hallucination: plan text only names valid tools
    hallucinated = False
    pred_text = " ".join(pred_steps).lower()
    # Look for "_tool" pattern that isn't a known tool
    found_tools_in_text = re.findall(r'\b\w+_tool\b', pred_text)
    for ft in found_tools_in_text:
        if ft not in {t.lower() for t in VALID_TOOLS}:
            hallucinated = True
            break
    score_no_halluc = 0 if hallucinated else 1

    total = (score_valid + score_step + score_tools + score_no_halluc) / 4

    return {
        "valid_json":       score_valid,
        "step_count_match": score_step,
        "tool_coverage":    round(score_tools, 3),
        "no_hallucination": score_no_halluc,
        "total":            round(total, 3),
    }


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Benchmark Planner Agent")
    parser.add_argument("--model",    default="gpt-4o-mini",  help="Model name")
    parser.add_argument("--provider", default="openai",       help="openai | groq | ollama")
    args = parser.parse_args()

    # Load dataset
    if not os.path.exists(DATASET_PATH):
        logger.error(f"Dataset not found at {DATASET_PATH}. Run generate_planner_dataset.py first.")
        return

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    logger.info(f"Loaded {len(records)} test cases from {DATASET_PATH}")
    logger.info(f"Benchmarking model : {args.model}  (provider: {args.provider})")
    logger.info(f"Today              : {TODAY}\n")

    llm = build_llm(args.model, args.provider)

    results = []
    category_scores: dict[str, list] = {}

    for rec in records:
        qid      = rec["id"]
        query    = rec["query"]
        category = rec["category"]
        history  = rec["chat_history"]

        logger.info(f"[{qid:02d}/{len(records)}] [{category.upper()}] {query[:70]}")

        pred_steps, latency_ms, valid_json = run_planner(llm, query, history)
        scores = score_result(rec, pred_steps, valid_json)

        logger.info(
            f"  Steps: {len(pred_steps)} (gold: {len(rec['gpt_plan'])}) | "
            f"Latency: {latency_ms} ms | Score: {scores['total']:.2%}"
        )
        for i, s in enumerate(pred_steps, 1):
            logger.info(f"    Step {i}: {s}")

        result = {
            "id":              qid,
            "query":           query,
            "category":        category,
            "gold_plan":       rec["gpt_plan"],
            "pred_plan":       pred_steps,
            "gold_latency_ms": rec["gpt_latency_ms"],
            "pred_latency_ms": latency_ms,
            "scores":          scores,
        }
        results.append(result)
        category_scores.setdefault(category, []).append(scores["total"])
        logger.info("")

    # ── Aggregate ─────────────────────────────────────────────────────────────
    all_scores    = [r["scores"]["total"] for r in results]
    all_latencies = [r["pred_latency_ms"] for r in results]
    gold_latencies = [r["gold_latency_ms"] for r in results if r["gold_latency_ms"] > 0]

    avg_score   = sum(all_scores) / len(all_scores)
    avg_latency = round(sum(all_latencies) / len(all_latencies))
    avg_gold_lat = round(sum(gold_latencies) / len(gold_latencies)) if gold_latencies else 0

    header = f"  {args.model}  vs  gpt-4o-mini (gold)  |  {TODAY}"
    sep    = "=" * max(60, len(header) + 4)

    print(f"\n{sep}")
    print(header)
    print(sep)
    print(f"  {'Metric':<28}  {'Model':>10}  {'Gold':>10}")
    print(f"  {'-'*28}  {'-'*10}  {'-'*10}")
    print(f"  {'Avg Overall Score':<28}  {avg_score:>9.1%}  {'(baseline)':>10}")
    print(f"  {'Avg Latency (ms)':<28}  {avg_latency:>10}  {avg_gold_lat:>10}")

    print(f"\n  {'Score by Category':}")
    for cat, scores in sorted(category_scores.items()):
        cat_avg = sum(scores) / len(scores)
        print(f"    {cat:<18} {cat_avg:>8.1%}  ({len(scores)} queries)")

    # Per-metric breakdown
    for metric in ["valid_json", "step_count_match", "tool_coverage", "no_hallucination"]:
        vals = [r["scores"][metric] for r in results]
        avg  = sum(vals) / len(vals)
        print(f"  {'  '+metric:<28}  {avg:>9.1%}")

    print(sep)

    # ── Save results ──────────────────────────────────────────────────────────
    safe_name  = re.sub(r"[^a-zA-Z0-9_\-]", "_", args.model)
    out_path   = f"dataset/planner_benchmark_results_{safe_name}.json"
    summary = {
        "model":          args.model,
        "provider":       args.provider,
        "date":           TODAY,
        "total_queries":  len(records),
        "avg_score":      round(avg_score, 4),
        "avg_latency_ms": avg_latency,
        "gold_avg_latency_ms": avg_gold_lat,
        "category_scores": {k: round(sum(v)/len(v), 4) for k, v in category_scores.items()},
        "results":        results,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n  Full results saved to: {out_path}\n")


if __name__ == "__main__":
    main()
