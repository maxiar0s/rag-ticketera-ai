import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    documents: List[str]
    sources: List[Dict[str, Any]]
    complexity_tier: str
    user_id: Optional[int]
    channel_user_id: Optional[str]
    conversation_id: str
    final_response: str
