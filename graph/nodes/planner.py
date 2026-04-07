from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from graph.state import AgentState
from config import OPENAI_API_KEY, OPENAI_MODEL

from datetime import date

class Plan(BaseModel):
    steps: List[str] = Field(description="A step-by-step plan to accomplish the user's request.")

planner_llm = ChatOpenAI(
    api_key=OPENAI_API_KEY, 
    model=OPENAI_MODEL, 
    temperature=0
).with_structured_output(Plan)

def get_planner_prompt():
    return f"""You are PennyWise's Planner Agent. Today is {date.today().isoformat()}.
Your job is to break down the user's request into a concrete plan using the available tools.
If the request is a simple conversation, the plan should just be a single step: 'Respond to user contextually'.

Valid Categories:
    "food", "shopping", "commute", "travel", "entertainment", "health", "utilities", "salary", "gift", "investment", "other"

Available tools:
1. prepare_log_expense: Extract transaction details to log an expense or income.
2. read_expenses_tool: Query the SQLite database for past transactions.
3. set_budget_tool: Set or update a budget.
4. read_budgets_tool: Queries the database to list the user's current budgets.

Provide the smallest number of logical steps required."""

def planner_node(state: AgentState) -> Dict[str, Any]:
    input_text = state['input']
    history = state.get('chat_history', [])
    
    messages = [SystemMessage(content=get_planner_prompt())]
    if history:
        messages.extend(history)
    messages.append(HumanMessage(content=input_text))
    
    plan_obj = planner_llm.invoke(messages)
    
    print(f"[PLANNER] Created Plan with {len(plan_obj.steps)} steps: {plan_obj.steps}")
    
    return {
        "plan": plan_obj.steps,
        "past_steps": [] # reset past steps for the new plan
    }
