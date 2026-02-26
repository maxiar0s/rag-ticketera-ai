import os
from urllib.parse import quote_plus

from langgraph.checkpoint.memory import MemorySaver


def _build_postgres_dsn() -> str:
    explicit_dsn = os.getenv("RAG_MEMORY_POSTGRES_DSN", "").strip()
    if explicit_dsn:
        return explicit_dsn

    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    dbname = os.getenv("POSTGRES_DB", "rag_knowledge_base")
    user = quote_plus(os.getenv("POSTGRES_USER", "rag_user"))
    password = quote_plus(os.getenv("POSTGRES_PASSWORD", "rag_password_dev"))

    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


def build_checkpointer():
    memory_backend = os.getenv("RAG_MEMORY_BACKEND", "postgres").strip().lower()

    if memory_backend == "memory":
        print("🧠 Checkpointer configurado en memoria (no persistente)", flush=True)
        return MemorySaver()

    try:
        from langgraph.checkpoint.postgres import PostgresSaver

        dsn = _build_postgres_dsn()
        checkpointer = PostgresSaver.from_conn_string(dsn)
        if hasattr(checkpointer, "setup"):
            checkpointer.setup()
        print("🧠 Checkpointer PostgreSQL activo (persistente)", flush=True)
        return checkpointer
    except Exception as exc:  # noqa: BLE001
        print(
            "⚠️  No se pudo inicializar checkpointer PostgreSQL; "
            "se usará memoria no persistente. "
            f"Detalle: {exc}",
            flush=True,
        )
        return MemorySaver()
