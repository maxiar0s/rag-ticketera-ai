from langgraph.graph import StateGraph, END
from app.utils.state import AgentState
from app.utils.nodes import retrieve_node, generate_node

# Definimos el flujo
workflow = StateGraph(AgentState)

workflow.add_node("retriever", retrieve_node)
workflow.add_node("generator", generate_node)

workflow.set_entry_point("retriever")
workflow.add_edge("retriever", "generator")
workflow.add_edge("generator", END)

# Compilamos
graph_app = workflow.compile()