from langchain_core.tools import tool

from app.agent.tools.db_common import run_query


@tool
def obtener_detalle_ticket(ticket_id: int):
    """
    Obtiene detalle resumido de un ticket por ID.
    """
    print(f"--- 🛠️ TOOL obtener_detalle_ticket({ticket_id}) ---", flush=True)

    if not ticket_id:
        return "Debes indicar ticket_id."

    try:
        rows = run_query(
            """
            SELECT
              t.id,
              t.titulo,
              t.descripcion,
              t.estadoTicket,
              t.prioridad,
              t.fuente,
              t.createdAt,
              cm.razonSocial as cliente,
              s.sucursal
            FROM Tickets t
            LEFT JOIN CasasMatrices cm ON cm.id = t.casaMatrizId
            LEFT JOIN Sucursales s ON s.id = t.sucursalId
            WHERE t.id = %s
            LIMIT 1;
            """,
            (ticket_id,),
        )

        if not rows:
            return "No se encontró el ticket indicado."

        return rows[0]
    except Exception as exc:  # noqa: BLE001
        return f"Error obteniendo detalle de ticket: {exc}"
