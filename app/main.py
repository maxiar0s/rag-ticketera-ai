import os
from contextlib import asynccontextmanager
from typing import Literal, Optional

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Security,
    status,
)
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from app.agent.graph import graph_app as utils_app
from langchain_core.messages import HumanMessage
from app.infrastructure.vector_store import VectorStore
from app.indexing.ingest_biblioteca import (
    delete_project_from_index,
    run_ingest,
    run_ingest_for_project,
)

# --- CONFIGURACIÓN & SEGURIDAD ---
API_KEY_SECRET = os.getenv("RAG_API_KEY", "dev_secret")
SYNC_WEBHOOK_SECRET = os.getenv("RAG_SYNC_WEBHOOK_SECRET", API_KEY_SECRET)
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)
MEMORY_SCOPE = os.getenv("RAG_MEMORY_SCOPE", "conversation").strip().lower()



async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY_SECRET:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Credenciales inválidas. Acceso denegado al Cerebro IA.",
    )


async def verify_sync_secret(x_webhook_secret: str = Header(default="")):
    if x_webhook_secret == SYNC_WEBHOOK_SECRET:
        return x_webhook_secret
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Webhook de sincronizacion no autorizado.",
    )


# --- MODELOS ---
class TicketRequest(BaseModel):
    subject: str
    content: str
    user_id: Optional[int] = None
    channel_user_id: Optional[str] = None
    conversation_id: Optional[str] = None


class KBSyncRequest(BaseModel):
    action: Literal["incremental", "full_reindex", "upsert", "delete"] = "incremental"
    project_id: Optional[int] = None
    chunk_size: int = 900
    overlap: int = 150
    triggered_by: str = "unknown"


def _resolve_conversation_id(ticket: TicketRequest) -> str:
    # Scope "user": comparte memoria entre canales si el user_id backend coincide.
    if MEMORY_SCOPE == "user" and ticket.user_id:
        return f"user_{ticket.user_id}"

    # Scope por conversación/canal (default).
    return (
        ticket.conversation_id
        or (f"channel_{ticket.channel_user_id}" if ticket.channel_user_id else None)
        or (f"user_{ticket.user_id}" if ticket.user_id else None)
        or "anon"
    )


def _run_sync_job(payload: KBSyncRequest):
    print(
        f"[KB Sync] Iniciando job action={payload.action} project_id={payload.project_id} triggered_by={payload.triggered_by}",
        flush=True,
    )
    try:
        if payload.action == "upsert":
            if payload.project_id is None:
                raise ValueError("project_id es requerido para action=upsert")
            result = run_ingest_for_project(
                project_id=payload.project_id,
                chunk_size=payload.chunk_size,
                overlap=payload.overlap,
            )
        elif payload.action == "delete":
            if payload.project_id is None:
                raise ValueError("project_id es requerido para action=delete")
            result = delete_project_from_index(project_id=payload.project_id)
        elif payload.action == "full_reindex":
            result = run_ingest(
                full_reindex=True,
                chunk_size=payload.chunk_size,
                overlap=payload.overlap,
            )
        else:
            result = run_ingest(
                full_reindex=False,
                chunk_size=payload.chunk_size,
                overlap=payload.overlap,
            )

        print(f"[KB Sync] Job completado: {result}", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"[KB Sync] Error en job: {exc}", flush=True)


class KBSyncRequest(BaseModel):
    action: Literal["incremental", "full_reindex", "upsert", "delete"] = "incremental"
    project_id: Optional[int] = None
    chunk_size: int = 900
    overlap: int = 150
    triggered_by: str = "unknown"


def _run_sync_job(payload: KBSyncRequest):
    print(
        f"[KB Sync] Iniciando job action={payload.action} project_id={payload.project_id} triggered_by={payload.triggered_by}",
        flush=True,
    )
    try:
        if payload.action == "upsert":
            if payload.project_id is None:
                raise ValueError("project_id es requerido para action=upsert")
            result = run_ingest_for_project(
                project_id=payload.project_id,
                chunk_size=payload.chunk_size,
                overlap=payload.overlap,
            )
        elif payload.action == "delete":
            if payload.project_id is None:
                raise ValueError("project_id es requerido para action=delete")
            result = delete_project_from_index(project_id=payload.project_id)
        elif payload.action == "full_reindex":
            result = run_ingest(
                full_reindex=True,
                chunk_size=payload.chunk_size,
                overlap=payload.overlap,
            )
        else:
            result = run_ingest(
                full_reindex=False,
                chunk_size=payload.chunk_size,
                overlap=payload.overlap,
            )

        print(f"[KB Sync] Job completado: {result}", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"[KB Sync] Error en job: {exc}", flush=True)



class KBSyncRequest(BaseModel):
    action: Literal["incremental", "full_reindex", "upsert", "delete"] = "incremental"
    project_id: Optional[int] = None
    chunk_size: int = 900
    overlap: int = 150
    triggered_by: str = "unknown"


def _run_sync_job(payload: KBSyncRequest):
    print(
        f"[KB Sync] Iniciando job action={payload.action} project_id={payload.project_id} triggered_by={payload.triggered_by}",
        flush=True,
    )
    try:
        if payload.action == "upsert":
            if payload.project_id is None:
                raise ValueError("project_id es requerido para action=upsert")
            result = run_ingest_for_project(
                project_id=payload.project_id,
                chunk_size=payload.chunk_size,
                overlap=payload.overlap,
            )
        elif payload.action == "delete":
            if payload.project_id is None:
                raise ValueError("project_id es requerido para action=delete")
            result = delete_project_from_index(project_id=payload.project_id)
        elif payload.action == "full_reindex":
            result = run_ingest(
                full_reindex=True,
                chunk_size=payload.chunk_size,
                overlap=payload.overlap,
            )
        else:
            result = run_ingest(
                full_reindex=False,
                chunk_size=payload.chunk_size,
                overlap=payload.overlap,
            )

        print(f"[KB Sync] Job completado: {result}", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"[KB Sync] Error en job: {exc}", flush=True)


# --- CICLO DE VIDA (DB) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Iniciando Microservicio AI...")
    try:
        VectorStore().ensure_schema()
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️  No se pudo verificar schema vectorial: {exc}", flush=True)
    yield
    print("🛑 Apagando...")


app = FastAPI(title="Ticketera AI Agent", lifespan=lifespan)


# --- ENDPOINTS ---
@app.post("/agent/process", dependencies=[Depends(verify_api_key)])
async def process_ticket(ticket: TicketRequest):
    """
    Endpoint corregido para hablar con LangGraph.
    """
    # 1. Convertimos el ticket en un Mensaje Humano para el Agente
    message_content = f"Asunto: {ticket.subject}\nContenido: {ticket.content}"

    # 2. Preparamos el estado inicial con las llaves EXACTAS que espera utils.py
    resolved_conversation_id = _resolve_conversation_id(ticket)

    inputs = {
        "messages": [HumanMessage(content=message_content)],
        "documents": [],
        "sources": [],
        "complexity_tier": "medium",
        "user_id": ticket.user_id,
        "channel_user_id": ticket.channel_user_id,
        "conversation_id": resolved_conversation_id,
        "final_response": "",
    }

    # 3. Invocamos el grafo
    print("🤖 Enviando ticket al cerebro...")
    result = await utils_app.ainvoke(
        inputs,
        config={"configurable": {"thread_id": resolved_conversation_id}},
    )

    # 4. Devolvemos solo lo que existe en el resultado
    return {"solution": result["final_response"], "sources": result.get("sources", [])}


@app.post("/kb/sync", dependencies=[Depends(verify_sync_secret)])
async def kb_sync(payload: KBSyncRequest, background_tasks: BackgroundTasks):
    if payload.action in {"upsert", "delete"} and payload.project_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="project_id es obligatorio para acciones upsert/delete",
        )

    background_tasks.add_task(_run_sync_job, payload)
    return {
        "accepted": True,
        "action": payload.action,
        "project_id": payload.project_id,
    }
