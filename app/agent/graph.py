from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.nodes.classify import classify_node
from app.agent.nodes.generate import generate_node
from app.agent.nodes.retrieve import retrieve_node
from app.agent.state import AgentState
from app.agent.tools import consultar_mis_tickets
from app.infrastructure.checkpointer import build_checkpointer


workflow = StateGraph(AgentState)
checkpointer = build_checkpointer()

workflow.add_node("retriever", retrieve_node)
workflow.add_node("classifier", classify_node)
workflow.add_node("generator", generate_node)
workflow.add_node("tools", ToolNode([consultar_mis_tickets]))

workflow.set_entry_point("retriever")
workflow.add_edge("retriever", "classifier")
workflow.add_edge("classifier", "generator")
workflow.add_conditional_edges("generator", tools_condition)
workflow.add_edge("tools", "generator")

graph_app = workflow.compile(checkpointer=checkpointer)
