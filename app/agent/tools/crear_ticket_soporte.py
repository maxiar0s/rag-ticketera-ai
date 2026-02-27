from datetime import datetime

from langchain_core.tools import tool

from app.agent.tools.db_common import (
    VALID_PRIORITIES,
    VALID_SOURCES,
    resolve_default_ia_client_id,
    run_query,
    run_write,
)


@tool
def crear_ticket_soporte(
    user_id: int,
    descripcion: str,
    casa_matriz_id: str = "",
    titulo: str = "",
    prioridad: str = "Media",
    sucursal_id: str = "",
    fuente: str = "Agente IA",
):
    """
    Crea un ticket en estado Nuevo.
    Requiere user_id autenticado, cliente (casa_matriz_id) y descripcion.
    """
    print(
        f"--- 🛠️ TOOL crear_ticket_soporte(user_id={user_id}, casa_matriz_id={casa_matriz_id}) ---",
        flush=True,
    )

    if not user_id:
        return "No puedo crear ticket: user_id no disponible."

    cliente_id = (casa_matriz_id or "").strip()
    default_client_used = False
    if not cliente_id:
        cliente_id = resolve_default_ia_client_id() or ""
        default_client_used = bool(cliente_id)

    if not cliente_id:
        return (
            "Falta casa_matriz_id para crear el ticket y no encontré cliente por defecto IA. "
            "Configura RAG_DEFAULT_IA_CLIENT_ID o crea Casa Matriz 'Agente AI'."
        )

    descripcion_limpia = (descripcion or "").strip()
    if len(descripcion_limpia) < 5:
        return "La descripcion debe tener al menos 5 caracteres."

    prioridad_limpia = (prioridad or "Media").strip().title()
    if prioridad_limpia not in VALID_PRIORITIES:
        prioridad_limpia = "Media"

    fuente_limpia = (fuente or "Agente IA").strip()
    if fuente_limpia not in VALID_SOURCES:
        fuente_limpia = "Agente IA"

    try:
        cliente = run_query(
            "SELECT id, razonSocial FROM CasasMatrices WHERE id = %s LIMIT 1;",
            (cliente_id,),
        )
        if not cliente:
            return "No pude crear el ticket: el cliente indicado no existe."

        sucursal_final = None
        sucursal_candidate = (sucursal_id or "").strip()
        if sucursal_candidate:
            sucursal = run_query(
                """
                SELECT id FROM Sucursales
                WHERE id = %s AND casaMatrizId = %s
                LIMIT 1;
                """,
                (sucursal_candidate, cliente_id),
            )
            if not sucursal:
                return "No pude crear el ticket: la sucursal no pertenece al cliente indicado."
            sucursal_final = sucursal_candidate

        creador = run_query(
            "SELECT id, email FROM Cuentas WHERE id = %s LIMIT 1;",
            (user_id,),
        )
        if not creador:
            return "No pude crear el ticket: usuario creador no encontrado."

        creator_email = (creador[0].get("email") or "").strip() or None
        titulo_limpio = (titulo or "").strip() or None
        now = datetime.utcnow()

        ticket_id = run_write(
            """
            INSERT INTO Tickets (
              titulo,
              descripcion,
              tecnicos,
              tecnicoAsignadoId,
              fechaVisita,
              casaMatrizId,
              sucursalId,
              creadoPorId,
              actualizadoPorId,
              estadoTicket,
              prioridad,
              fuente,
              creatorEmail,
              createdAt,
              updatedAt
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                titulo_limpio,
                descripcion_limpia,
                "[]",
                None,
                now.date().isoformat(),
                cliente_id,
                sucursal_final,
                user_id,
                user_id,
                "Nuevo",
                prioridad_limpia,
                fuente_limpia,
                creator_email,
                now,
                now,
            ),
        )

        return {
            "ticket_id": ticket_id,
            "estado": "Nuevo",
            "prioridad": prioridad_limpia,
            "fuente": fuente_limpia,
            "cliente": cliente[0],
            "default_client_used": default_client_used,
        }
    except Exception as exc:  # noqa: BLE001
        return f"Error creando ticket: {exc}"
