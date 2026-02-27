from langchain_core.tools import tool

from app.agent.tools.db_common import run_query


@tool
def consultar_mis_tickets(user_id: int):
    """
    Consulta tickets activos asignados a un usuario.
    Retorna ID, asunto, estado, prioridad y fecha de creación.
    """
    print(f"--- 🛠️ TOOL consultar_mis_tickets({user_id}) ---", flush=True)

    if not user_id:
        return "No se pudo consultar tickets: user_id no disponible."

    try:
        results = run_query(
            """
            SELECT
                id,
                titulo as subject,
                estadoTicket as status,
                prioridad as priority,
                createdAt as created_at
            FROM Tickets
            WHERE tecnicoAsignadoId = %s
              AND estadoTicket IN ('Nuevo', 'Abierto', 'En espera', 'Pendiente', 'En Progreso')
            ORDER BY prioridad DESC, createdAt ASC;
            """,
            (user_id,),
        )

        if not results:
            return "No se encontraron tickets activos asignados a este usuario."

        return results
    except Exception as exc:  # noqa: BLE001
        return f"Error al consultar la base de datos: {exc}"
