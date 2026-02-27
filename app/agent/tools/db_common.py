import os
from typing import Any, Dict, List, Optional

from app.infrastructure.mysql import get_db_connection


VALID_PRIORITIES = {"Baja", "Media", "Alta"}
VALID_SOURCES = {"Web", "Email", "Telegram IA", "Agente IA"}
DEFAULT_IA_CLIENT_NAME = os.getenv("RAG_DEFAULT_IA_CLIENT_NAME", "Agente AI").strip()


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


def resolve_default_ia_client_id() -> Optional[str]:
    configured_id = os.getenv("RAG_DEFAULT_IA_CLIENT_ID", "").strip()
    if configured_id:
        rows = run_query(
            "SELECT id FROM CasasMatrices WHERE id = %s LIMIT 1;",
            (configured_id,),
        )
        if rows:
            return str(rows[0]["id"])

    if not DEFAULT_IA_CLIENT_NAME:
        return None

    rows = run_query(
        """
        SELECT id
        FROM CasasMatrices
        WHERE LOWER(TRIM(razonSocial)) = LOWER(TRIM(%s))
        LIMIT 1;
        """,
        (DEFAULT_IA_CLIENT_NAME,),
    )
    if rows:
        return str(rows[0]["id"])

    return None
