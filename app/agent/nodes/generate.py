from langchain_core.messages import SystemMessage

from app.agent.nodes.llm_config import llm_router
from app.agent.state import AgentState


def generate_node(state: AgentState):
    print("--- 🧠 NODE: GENERATE (LLM) ---")

    docs_text = "\n".join(state["documents"])
    messages = state["messages"]
    complexity_tier = (state.get("complexity_tier") or "medium").strip().lower()
    current_user_id = state.get("user_id")
    current_channel_user_id = state.get("channel_user_id")
    current_conversation_id = state.get("conversation_id")

    system_prompt = SystemMessage(
        content=f"""
    Eres un Agente de Soporte Técnico experto. Tienes acceso a una base de datos SQL mediante herramientas.

    CONTEXTO DE IDENTIDAD:
    - user_id autenticado: {current_user_id}
    - channel_user_id: {current_channel_user_id}
    - conversation_id: {current_conversation_id}

    TUS INSTRUCCIONES PRIORITARIAS:
    1. Si el usuario pregunta por sus "tickets", "pendientes" o "estado", **DEBES** usar la herramienta 'consultar_mis_tickets' inmediatamente con el user_id autenticado del contexto, sin pedir que el usuario lo reingrese.
    2. NO respondas con texto genérico si la pregunta requiere datos del usuario. PRIMERO usa la herramienta.
    3. Si la herramienta devuelve resultados, úsalos para responder.
    4. Usa el 'CONTEXTO TÉCNICO' (RAG) solo para preguntas generales (ej: cómo reiniciar router). Para datos del usuario, usa la herramienta.
    5. Si en el historial ya existe resultado de herramienta con tickets, responde con los tickets concretos (ID, asunto, estado, prioridad).
    6. NO respondas con frases meta como "la respuesta es..."; entrega directamente la información final al usuario.

    CONTEXTO TÉCNICO (RAG):
    {docs_text}
    """
    )

    response = llm_router.invoke([system_prompt] + messages, tier=complexity_tier)

    print(f"🔍 DEBUG - LLM Response Content: {response.content}")
    print(f"🛠️ DEBUG - LLM Tool Calls: {response.tool_calls}")
    print(f"💸 DEBUG - Complexity tier: {complexity_tier}", flush=True)

    return {"messages": [response], "final_response": response.content}
