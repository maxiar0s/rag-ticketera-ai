from datetime import datetime

from langchain_core.tools import tool

from app.infrastructure.mysql import get_db_connection
from app.agent.tools.db_common import run_query


@tool
def agregar_comentario_interno_ticket(ticket_id: int, user_id: int, comentario: str):
    """
    Agrega o reemplaza el comentario interno del ticket.
    """
    print(
        f"--- 🛠️ TOOL agregar_comentario_interno_ticket(ticket_id={ticket_id}, user_id={user_id}) ---",
        flush=True,
    )

    if not ticket_id:
        return "Debes indicar ticket_id."
    if not user_id:
        return "Debes indicar user_id para registrar el comentario."

    texto = (comentario or "").strip()
    if len(texto) < 2:
        return "El comentario debe tener al menos 2 caracteres."

    try:
        ticket = run_query("SELECT id FROM Tickets WHERE id = %s LIMIT 1;", (ticket_id,))
        if not ticket:
            return "No se encontró el ticket indicado."

        conn = get_db_connection()
        cursor = None
        if conn is None:
            return "conexion no disponible"
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE Tickets
                SET comentarioInterno = %s,
                    actualizadoPorId = %s,
                    updatedAt = %s
                WHERE id = %s;
                """,
                (texto, user_id, datetime.utcnow(), ticket_id),
            )
            conn.commit()
        finally:
            if cursor is not None:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

        return {
            "ok": True,
            "ticket_id": ticket_id,
            "mensaje": "Comentario interno actualizado.",
        }
    except Exception as exc:  # noqa: BLE001
        return f"Error actualizando comentario interno: {exc}"
