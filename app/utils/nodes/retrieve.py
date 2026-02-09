from app.utils.state import AgentState

def retrieve_node(state: AgentState):
    """
    Simula la búsqueda (Mockup RAG)
    """
    print("--- 🔍 NODE: RETRIEVE ---", flush=True)
    # Nota: Asegúrate de que state['messages'] tenga contenido antes de acceder a [-1]
    query = state['messages'][-1].content
    
    found_docs = [
        "Manual Redes: Si la luz roja parpadea, intente reiniciar el router.",
        "Soporte N2: Error 500 en servidor suele requerir revisar logs de Apache/Nginx."
    ]
    return {"documents": found_docs}