from langchain_core.messages import SystemMessage
from app.utils.state import AgentState

# Importamos la configuración del modelo desde el archivo hermano
from .llm_config import llm


def generate_node(state: AgentState):
    """
    Genera respuesta usando Gemini + Contexto
    """
    print("--- 🧠 NODE: GENERATE (LLM) ---")

    docs_text = "\n".join(state["documents"])
    messages = state["messages"]

    # Prompt del sistema reforzado para forzar el uso de herramientas
    system_prompt = SystemMessage(
        content=f"""
    Eres un Agente de Soporte Técnico experto. Tienes acceso a una base de datos SQL mediante herramientas.

    TUS INSTRUCCIONES PRIORITARIAS:
    1. Si el usuario se identifica (ej: "soy el usuario 1") y pregunta por sus "tickets", "pendientes" o "estado", **DEBES** usar la herramienta 'consultar_mis_tickets' inmediatamente.
    2. NO respondas con texto genérico si la pregunta requiere datos del usuario. PRIMERO usa la herramienta.
    3. Si la herramienta devuelve resultados, úsalos para responder.
    4. Usa el 'CONTEXTO TÉCNICO' (RAG) solo para preguntas generales (ej: cómo reiniciar router). Para datos del usuario, usa la herramienta.
    5. Si en el historial ya existe resultado de herramienta con tickets, responde con los tickets concretos (ID, asunto, estado, prioridad).
    6. NO respondas con frases meta como "la respuesta es..."; entrega directamente la información final al usuario.

    CONTEXTO TÉCNICO (RAG):
    {docs_text}
    """
    )

    # Invocamos al modelo con el prompt de sistema + historial de mensajes
    response = llm.invoke([system_prompt] + messages)

    # --- LOGGING DE DEPURACIÓN ---
    print(f"🔍 DEBUG - LLM Response Content: {response.content}")
    print(f"🛠️ DEBUG - LLM Tool Calls: {response.tool_calls}")
    # -----------------------------

    return {"messages": [response], "final_response": response.content}
