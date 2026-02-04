import operator
from typing import Annotated, List, TypedDict
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    # El historial de chat
    messages: Annotated[List[BaseMessage], operator.add]
    # Documentos recuperados (RAG context)
    documents: List[str]
    # Respuesta final string (opcional, pero útil para la API)
    final_response: str