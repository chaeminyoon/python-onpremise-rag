from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    State for the Reasoning Graph.
    """
    input: str
    chat_history: List[BaseMessage]
    context: List[str]  # List of retrieved context strings
    answer: str
    current_decision: Optional[Dict[str, Any]] # To store Router's JSON output
