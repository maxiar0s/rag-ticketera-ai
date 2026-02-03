import operator
from typing import Annotated, List, TypedDict

# Importaciones de LangChain Core (Mensajes y Prompt)
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
# Importamos StateGraph para definir la máquina de estados
from langgraph.graph import StateGraph, END

# --- 1. DEFINICIÓN DEL ESTADO (MEMORIA) ---
class AgentState(TypedDict):
    # 'messages': Lista de mensajes. 
    # Usamos operator.add para que cuando un nodo devuelva un mensaje,
    # este se AÑADA a la lista en lugar de sobrescribirla.
    messages: Annotated[List[BaseMessage], operator.add]
    # Contexto extra recuperado (RAG)
    documents: List[str]
    # Respuesta final estructurada
    final_response: str

# --- 2. NODOS (LAS ACCIONES) ---

def retrieve_node(state: AgentState):
    """
    Simula la búsqueda vectorial (RAG).
    Fase 5: Aquí conectaremos pgvector real.
    """
    print("--- 🔍 NODE: RETRIEVE ---")
    # Obtenemos el último mensaje del usuario
    last_message = state['messages'][-1].content
    
    # Mockup: Simulamos encontrar docs relevantes en la BD
    found_docs = [
        f"Doc A: Para problemas de '{last_message}', intente reiniciar el servicio.",
        "Doc B: Si es un error 500, revise los logs de Nginx."
    ]
    
    # Retornamos SOLO lo que queremos actualizar en el estado
    return {"documents": found_docs}

def generate_node(state: AgentState):
    """
    Genera la respuesta final usando los documentos recuperados.
    """
    print("--- 🧠 NODE: GENERATE ---")
    docs = "\n".join(state['documents'])
    messages = state['messages']
    
    # Mockup: Simulamos la respuesta de un LLM (GPT-4/Llama3)
    # En producción: response = llm.invoke(prompt)
    reasoning = f"Basado en los documentos: {docs}"
    response_text = "Te sugiero reiniciar el servicio como primer paso."
    
    # Devolvemos un AIMessage que se añadirá a la lista 'messages'
    return {
        "messages": [AIMessage(content=response_text)],
        "final_response": response_text
    }

# --- 3. CONSTRUCCIÓN DEL GRAFO ---

workflow = StateGraph(AgentState)

# Añadimos los nodos al mapa
workflow.add_node("retriever", retrieve_node)
workflow.add_node("generator", generate_node)

# Definimos el flujo (El camino)
# Entrada -> Retriever -> Generator -> FIN
workflow.set_entry_point("retriever")
workflow.add_edge("retriever", "generator")
workflow.add_edge("generator", END)

# Compilamos el grafo para que sea ejecutable
agent_app = workflow.compile()