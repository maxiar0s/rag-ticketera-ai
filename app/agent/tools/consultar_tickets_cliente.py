from langchain_core.tools import tool

from app.agent.tools.db_common import run_query


@tool
def consultar_tickets_cliente(casa_matriz_id: str, estado: str = ""):
    """
    Lista tickets de un cliente, opcionalmente filtrando por estado.
    """
    print(
        f"--- 🛠️ TOOL consultar_tickets_cliente(casa_matriz_id={casa_matriz_id}, estado={estado}) ---",
        flush=True,
    )

    cliente_id = (casa_matriz_id or "").strip()
    if not cliente_id:
        return "Debes indicar casa_matriz_id para consultar tickets del cliente."

    estado_limpio = (estado or "").strip()

    try:
        cliente = run_query(
            "SELECT id, razonSocial FROM CasasMatrices WHERE id = %s LIMIT 1;",
            (cliente_id,),
        )
        if not cliente:
            return "El cliente indicado no existe."

        if estado_limpio:
            rows = run_query(
                """
                SELECT id, titulo, estadoTicket, prioridad, fuente, createdAt
                FROM Tickets
                WHERE casaMatrizId = %s AND estadoTicket = %s
                ORDER BY createdAt DESC
                LIMIT 20;
                """,
                (cliente_id, estado_limpio),
            )
        else:
            rows = run_query(
                """
                SELECT id, titulo, estadoTicket, prioridad, fuente, createdAt
                FROM Tickets
                WHERE casaMatrizId = %s
                ORDER BY createdAt DESC
                LIMIT 20;
                """,
                (cliente_id,),
            )

        if not rows:
            return "No se encontraron tickets para ese cliente con los filtros indicados."

        return {
            "cliente": cliente[0],
            "tickets": rows,
        }
    except Exception as exc:  # noqa: BLE001
        return f"Error consultando tickets del cliente: {exc}"
