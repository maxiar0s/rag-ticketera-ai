from langchain_core.tools import tool

from app.infrastructure.mysql import get_db_connection


@tool
def consultar_mis_tickets(user_id: int):
    """
    Consulta la base de datos SQL para encontrar los tickets asignados a un usuario especifico.
    Retorna una lista con el ID, asunto, estado y prioridad de los tickets activos.
    """
    print(f"--- 🛠️ TOOL EJECUTADA CON ID: {user_id} ---", flush=True)
    conn = get_db_connection()
    cursor = None
    if conn is None:
        return "Error al consultar la base de datos: conexión no disponible"
    try:
        cursor = conn.cursor(dictionary=True)

        query = """
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
        """

        cursor.execute(query, (user_id,))
        results = cursor.fetchall()

        if not results:
            return "No se encontraron tickets activos asignados a este usuario."

        return results

    except Exception as e:  # noqa: BLE001
        return f"Error al consultar la base de datos: {e}"
    finally:
        if cursor is not None:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
