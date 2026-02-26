from datetime import datetime

from langchain_core.tools import tool

from app.infrastructure.mysql import get_db_connection
from app.agent.tools.db_common import run_query


@tool
def asignar_tecnico_ticket(ticket_id: int, tecnico_id: int, user_id: int):
    """
    Asigna un tecnico a un ticket y actualiza el estado a Abierto si estaba en Nuevo.
    """
    print(
        f"--- 🛠️ TOOL asignar_tecnico_ticket(ticket_id={ticket_id}, tecnico_id={tecnico_id}, user_id={user_id}) ---",
        flush=True,
    )

    if not ticket_id or not tecnico_id or not user_id:
        return "Debes indicar ticket_id, tecnico_id y user_id."

    try:
        tecnico = run_query(
            "SELECT id, name, esTecnico FROM Cuentas WHERE id = %s LIMIT 1;",
            (tecnico_id,),
        )
        if not tecnico:
            return "No se encontró el técnico indicado."

        if int(tecnico[0].get("esTecnico") or 0) != 1:
            return "La cuenta indicada no corresponde a un técnico."

        ticket = run_query(
            "SELECT id, estadoTicket FROM Tickets WHERE id = %s LIMIT 1;",
            (ticket_id,),
        )
        if not ticket:
            return "No se encontró el ticket indicado."

        estado_actual = (ticket[0].get("estadoTicket") or "").strip()
        estado_nuevo = "Abierto" if estado_actual == "Nuevo" else estado_actual
        tecnicos_json = f"[\"{tecnico[0]['name']}\"]"

        conn = get_db_connection()
        cursor = None
        if conn is None:
            return "conexion no disponible"
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE Tickets
                SET tecnicoAsignadoId = %s,
                    tecnicos = %s,
                    estadoTicket = %s,
                    actualizadoPorId = %s,
                    updatedAt = %s
                WHERE id = %s;
                """,
                (tecnico_id, tecnicos_json, estado_nuevo, user_id, datetime.utcnow(), ticket_id),
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
            "tecnico": {
                "id": tecnico[0]["id"],
                "name": tecnico[0]["name"],
            },
            "estado": estado_nuevo,
            "mensaje": "Ticket asignado correctamente.",
        }
    except Exception as exc:  # noqa: BLE001
        return f"Error asignando técnico: {exc}"
