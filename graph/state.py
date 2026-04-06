from typing import TypedDict, Annotated, List, Any, Optional
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    input: str
    user_id: str
    chat_history: List[BaseMessage]
    messages: Annotated[List[BaseMessage], operator.add]
    plan: List[str]
    past_steps: Annotated[List[tuple], operator.add]
    error_count: int
    final_response: Optional[str]
