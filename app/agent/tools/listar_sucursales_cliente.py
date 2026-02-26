from langchain_core.tools import tool

from app.agent.tools.db_common import run_query


@tool
def listar_sucursales_cliente(casa_matriz_id: str):
    """
    Lista las sucursales de un cliente para elegir correctamente el destino del ticket.
    """
    print(f"--- 🛠️ TOOL listar_sucursales_cliente({casa_matriz_id}) ---", flush=True)

    cliente_id = (casa_matriz_id or "").strip()
    if not cliente_id:
        return "Debes indicar casa_matriz_id para listar sucursales."

    try:
        exists = run_query(
            "SELECT id, razonSocial FROM CasasMatrices WHERE id = %s LIMIT 1;",
            (cliente_id,),
        )
        if not exists:
            return "El cliente indicado no existe."

        rows = run_query(
            """
            SELECT
              id,
              sucursal,
              direccion,
              estado
            FROM Sucursales
            WHERE casaMatrizId = %s
            ORDER BY sucursal ASC;
            """,
            (cliente_id,),
        )

        return {
            "cliente": exists[0],
            "sucursales": rows,
        }
    except Exception as exc:  # noqa: BLE001
        return f"Error al listar sucursales: {exc}"
