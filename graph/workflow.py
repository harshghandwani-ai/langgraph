from langgraph.graph import StateGraph, END, START
from graph.state import AgentState
from graph.nodes import planner_node, executor_node
from typing import Literal

def should_continue(state: AgentState) -> Literal["executor", "__end__"]:
    # If the executor node returned current_status done, or if the plan is fully executed, end.
    plan = state.get("plan", [])
    past_steps = state.get("past_steps", [])
    
    if state.get("current_status") == "done" or len(past_steps) >= len(plan):
        return "__end__"
    return "executor"

def create_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    
    # Add edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "executor")
    
    # Add conditional edges
    workflow.add_conditional_edges("executor", should_continue, {
        "executor": "executor",
        "__end__": END
    })
    
    # Removed memory saver since chat route manually manages history via SQLite
    graph = workflow.compile()
    
    return graph
