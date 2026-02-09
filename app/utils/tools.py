# app/utils/tools.py
from langchain_core.tools import tool
from app.utils.database import get_db_connection

@tool
def consultar_mis_tickets(user_id: int):
    """
    Consulta la base de datos SQL para encontrar los tickets asignados a un usuario específico.
    Retorna una lista con el ID, asunto, estado y prioridad de los tickets activos.
    """
    print(f"--- 🛠️ TOOL EJECUTADA CON ID: {user_id} ---", flush=True)
    conn = get_db_connection()
    try:
        # dictionary=True devuelve resultados como JSONs {'columna': valor}
        cursor = conn.cursor(dictionary=True) 
        
        # Seleccionamos solo las columnas críticas para la "vista general"
        query = """
        SELECT 
            id, 
            subject, 
            status, 
            priority, 
            created_at
        FROM tickets 
        WHERE assignee_id = %s 
        AND status IN ('OPEN', 'IN_PROGRESS', 'WAITING_CLIENT')
        ORDER BY priority DESC, created_at ASC;
        """
        
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        
        if not results:
            return "No se encontraron tickets activos asignados a este usuario."
            
        return results
        
    except Exception as e:
        return f"Error al consultar la base de datos: {e}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()