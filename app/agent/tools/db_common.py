from typing import Any, Dict, List

from app.infrastructure.mysql import get_db_connection


VALID_PRIORITIES = {"Baja", "Media", "Alta"}
VALID_SOURCES = {"Web", "Email", "Telegram IA"}


def run_query(query: str, params: tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = None
    if conn is None:
        raise RuntimeError("conexion no disponible")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def run_write(query: str, params: tuple[Any, ...]) -> int:
    conn = get_db_connection()
    cursor = None
    if conn is None:
        raise RuntimeError("conexion no disponible")

    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        if cursor is not None:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
