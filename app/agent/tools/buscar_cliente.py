from langchain_core.tools import tool

from app.agent.tools.db_common import run_query


@tool
def buscar_cliente(nombre_cliente: str):
    """
    Busca clientes por nombre o RUT y retorna candidatos para seleccionar uno.
    """
    print(f"--- 🛠️ TOOL buscar_cliente({nombre_cliente}) ---", flush=True)

    termino = (nombre_cliente or "").strip()
    if len(termino) < 2:
        return "Debes indicar al menos 2 caracteres para buscar cliente."

    try:
        results = run_query(
            """
            SELECT
              id,
              razonSocial,
              rut
            FROM CasasMatrices
            WHERE razonSocial LIKE %s OR rut LIKE %s
            ORDER BY razonSocial ASC
            LIMIT 10;
            """,
            (f"%{termino}%", f"%{termino}%"),
        )

        if not results:
            return "No encontré clientes con ese criterio."

        return results
    except Exception as exc:  # noqa: BLE001
        return f"Error al buscar cliente: {exc}"
