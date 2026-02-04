import os
from langchain_core.messages import AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.agent.state import AgentState

# --- CONFIGURACIÓN DEL MODELO ---
# Usamos Gemini 1.5 Flash. Temperatura 0 para respuestas técnicas y precisas.
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=os.environ.get("GOOGLE_API_KEY") # Tomará la key de las variables de entorno
)

def retrieve_node(state: AgentState):
    """
    Simula la búsqueda (Por ahora sigue siendo mockup hasta que conectemos Postgres)
    """
    print("--- 🔍 NODE: RETRIEVE ---")
    query = state['messages'][-1].content
    
    # Mockup RAG (Pronto conectaremos esto a vector-db)
    found_docs = [
        "Manual Redes: Si la luz roja parpadea, intente reiniciar el router.",
        "Soporte N2: Error 500 en servidor suele requerir revisar logs de Apache/Nginx."
    ]
    return {"documents": found_docs}

def generate_node(state: AgentState):
    """
    Genera respuesta usando Gemini 2.5 Flash + Contexto
    """
    print("--- 🧠 NODE: GENERATE (GEMINI) ---")
    
    # 1. Preparamos el contexto
    docs_text = "\n".join(state['documents'])
    messages = state['messages']
    
    # 2. Creamos el Prompt del Sistema (Instrucciones de personalidad)
    system_prompt = SystemMessage(content=f"""
    Eres un Agente de Soporte Técnico experto y empático.
    Usa el siguiente contexto recuperado para responder al usuario.
    Si la respuesta no está en el contexto, di que necesitas escalar el ticket.
    
    CONTEXTO TÉCNICO:
    {docs_text}
    """)
    
    # 3. Invocamos a Gemini (System Prompt + Historial de conversación)
    # LangChain concatena automáticamente el prompt del sistema con los mensajes del usuario
    response = llm.invoke([system_prompt] + messages)
    
    return {
        "messages": [response],
        "final_response": response.content
    }