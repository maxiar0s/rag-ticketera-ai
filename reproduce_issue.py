import os

# from dotenv import load_dotenv # Comentado para evitar errores si no está instalado
from langchain_core.messages import HumanMessage, SystemMessage
from app.agent.nodes.llm_config import llm

# No cargamos .env explícitamente, asumimos que Docker ya las tiene.
# Si corres local, asegúrate de tener GOOGLE_API_KEY seteada.


def test_tool_usage():
    print("--- TEST: Probando si el modelo usa la tool ---")

    # Simular el contexto que recibe el nodo generate
    system_prompt = SystemMessage(
        content="""
    Eres un Agente de Soporte Técnico experto. Tienes acceso a una base de datos SQL mediante herramientas.

    TUS INSTRUCCIONES PRIORITARIAS:
    1. Si el usuario se identifica (ej: "soy el usuario 1") y pregunta por sus "tickets", "pendientes" o "estado", **DEBES** usar la herramienta 'consultar_mis_tickets' inmediatamente.
    2. NO digas que no tienes información sin haber ejecutado primero la herramienta.
    """
    )

    # Mensaje del usuario
    user_message = HumanMessage(
        content="Hola, soy el usuario 1. ¿Qué tickets tengo pendientes?"
    )

    messages = [system_prompt, user_message]

    try:
        print("Modelo configurado: fallback multi-provider")
        response = llm.invoke(messages)
        print("\n--- REPUESTA DEL LLM ---")
        print(f"Content: {response.content}")
        print(f"Tool Calls: {response.tool_calls}")

        if response.tool_calls:
            print("\n✅ ÉXITO: El modelo intentó usar una herramienta.")
        else:
            print("\n❌ FALLO: El modelo NO usó ninguna herramienta.")

    except Exception as e:
        print(f"\n❌ ERROR DE EJECUCIÓN: {e}")


if __name__ == "__main__":
    test_tool_usage()
