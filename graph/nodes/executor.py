from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from graph.state import AgentState
from graph.tools import log_expense_tool, set_budget_tool, read_expenses_tool, read_budgets_tool
from config import OPENAI_API_KEY, OPENAI_MODEL
import json
from db import upsert_budget
from query_engine import execute_read_expenses

tools = [log_expense_tool, set_budget_tool, read_expenses_tool, read_budgets_tool]
executor_llm = ChatOpenAI(
    api_key=OPENAI_API_KEY, 
    model=OPENAI_MODEL, 
    temperature=0
).bind_tools(tools)

def executor_node(state: AgentState) -> Dict[str, Any]:
    plan = state['plan']
    past_steps = state.get('past_steps', [])
    user_id = state['user_id']
    history = state.get('chat_history', [])
    input_text = state['input']
    
    # Simple logic: If we have completed all steps, return
    if len(past_steps) >= len(plan):
        return {"current_status": "done"}
    
    current_step = plan[len(past_steps)]
    print(f"[EXECUTOR] Executing Step: {current_step}")
    
    from datetime import date
    
    messages = [SystemMessage(content=f"You are the execution agent. Today is {date.today().isoformat()}. Your task is to execute the current step: '{current_step}'.\nYou must use one of your tools if necessary. If not, just respond directly.")]
    if history:
        messages.extend(history)
    messages.append(HumanMessage(content=input_text))
    
    response = executor_llm.invoke(messages)
    
    tool_results = []
    response_texts = []
    
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            print(f"[EXECUTOR] Triggering Tool: {tool_name} with args {tool_args}")
            
            # Execute standard tools or custom logic
            if tool_name == "log_expense_tool":
                from graph.tools import log_expense_tool
                res = log_expense_tool.invoke(tool_args)
                tool_results.append((current_step, res))
                response_texts.append(res)
                
            elif tool_name == "set_budget_tool":
                amount = tool_args.get("amount")
                category = tool_args.get("category", "total")
                period = tool_args.get("period", "monthly")
                upsert_budget(user_id, category, amount, period)
                res = json.dumps({"status": "success", "message": f"Set {period} budget for {category} to {amount}"})
                tool_results.append((current_step, res))
                response_texts.append(res)
                
            elif tool_name == "read_expenses_tool":
                query = tool_args.get("query")
                db_res = execute_read_expenses(query, history=history, user_id=user_id)
                res = json.dumps({"status": "success", "db_result": db_res})
                tool_results.append((current_step, res))
                response_texts.append(res)
                
            elif tool_name == "read_budgets_tool":
                from db import get_budgets
                category = tool_args.get("category")
                budgets = get_budgets(user_id)
                if category and category.lower() != "total":
                    budgets = [b for b in budgets if b["category"].lower() == category.lower()]
                res = json.dumps({"status": "success", "db_result": json.dumps({"budgets": budgets})})
                tool_results.append((current_step, res))
                response_texts.append(res)
                
    else:
        # direct generation
        tool_results.append((current_step, response.content))
        response_texts.append(response.content)
        
    return {
        "past_steps": tool_results,
        "messages": [response],
        "final_response": response_texts[-1] if response_texts else None
    }
