from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from app.utils.state import AgentState
from app.utils.nodes.retrieve import retrieve_node
from app.utils.nodes.generate import generate_node
from app.utils.tools import consultar_mis_tickets

# 1. Definimos el grafo
workflow = StateGraph(AgentState)

# 2. Agregamos los nodos
workflow.add_node("retriever", retrieve_node)
workflow.add_node("generator", generate_node)
workflow.add_node("tools", ToolNode([consultar_mis_tickets]))

# 3. Conectamos las "tuberías" (aristas)

# Entrada -> Retriever
workflow.set_entry_point("retriever")

# Retriever -> Generator
workflow.add_edge("retriever", "generator")

# Generator -> CONDICIONAL (Aquí el guardia decide: ¿Tools o END?)
workflow.add_conditional_edges(
    "generator",  # Origen
    tools_condition,  # La lógica (Si hay tool -> "tools", si no -> END)
)

# Tools -> Generator (El ciclo de vuelta para leer la respuesta de la BD)
workflow.add_edge("tools", "generator")

# 4. Compilamos
graph_app = workflow.compile()
