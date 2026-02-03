from typing import TypedDict, List
from langgraph.graph import StateGraph, END

# 1. Definimos el Estado del Agente
# Es la "memoria" que pasa de un paso a otro.
class AgentState(TypedDict):
    ticket_subject: str
    ticket_content: str
    retrieved_docs: List[str]  # Documentos encontrados (RAG)
    final_response: str
    category: str

# 2. Definimos los Nodos (Las funciones de trabajo)

def retrieve_knowledge(state: AgentState):
    """
    Simulamos la búsqueda en la BD Vectorial (pgvector).
    En la próxima fase conectaremos esto con la conexión real a Postgres.
    """
    print(f"🔍 Buscando info para: {state['ticket_subject']}")
    # Mockup: Aquí iría la query a pgvector
    found_docs = [
        "Doc 1: Reiniciar router resuelve 80% problemas red.",
        "Doc 2: Error 500 usualmente es servidor caído."
    ]
    return {"retrieved_docs": found_docs}

def categorize_ticket(state: AgentState):
    """
    Analiza la urgencia y categoría.
    """
    print("🏷️ Categorizando ticket...")
    # Lógica simple por ahora
    category = "Soporte Nivel 1" if "router" in state['ticket_content'] else "Soporte Nivel 2"
    return {"category": category}

def generate_response(state: AgentState):
    """
    Genera la respuesta final usando los docs.
    """
    print("✍️ Redactando respuesta...")
    docs_text = "\n".join(state['retrieved_docs'])
    response = f"Basado en {docs_text}, sugiero revisar la conexión eléctrica."
    return {"final_response": response}

# 3. Construimos el Grafo
workflow = StateGraph(AgentState)

# Añadimos los nodos
workflow.add_node("retrieve", retrieve_knowledge)
workflow.add_node("categorize", categorize_ticket)
workflow.add_node("generate", generate_response)

# Definimos el flujo (Edges)
# Entrada -> Retrieve -> Categorize -> Generate -> FIN
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "categorize")
workflow.add_edge("categorize", "generate")
workflow.add_edge("generate", END)

# Compilamos el grafo
agent_app = workflow.compile()