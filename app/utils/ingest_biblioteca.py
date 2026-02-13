import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.utils.chunker import chunk_text, normalize_text

SOURCE_TYPE = "biblioteca_proyecto"
STATE_PATH = Path(__file__).resolve().parents[2] / "data" / "ingest_state.json"


def _load_state() -> Dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(state: Dict[str, Any]):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8"
    )


def _extract_sections(row: Dict[str, Any]) -> List[Dict[str, str]]:
    sections: List[Dict[str, str]] = []

    text_fields = {
        "nombre": row.get("nombre"),
        "descripcion": row.get("descripcion"),
        "instruccionesInstalacion": row.get("instruccionesInstalacion"),
        "instruccionesProd": row.get("instruccionesProd"),
        "manualUsuario": row.get("manualUsuario"),
        "notasTecnicas": row.get("notasTecnicas"),
        "linkRepositorio": row.get("linkRepositorio"),
    }

    for field_name, value in text_fields.items():
        clean_text = normalize_text(f"{value or ''}")
        if clean_text:
            sections.append({"section": field_name, "text": clean_text})

    contenido_raw = row.get("contenido")
    contenido_data: Dict[str, Any] = {}
    if isinstance(contenido_raw, dict):
        contenido_data = contenido_raw
    elif isinstance(contenido_raw, str) and contenido_raw.strip():
        try:
            parsed = json.loads(contenido_raw)
            if isinstance(parsed, dict):
                contenido_data = parsed
        except json.JSONDecodeError:
            contenido_data = {}

    for column_id, payload in contenido_data.items():
        if isinstance(payload, dict):
            text_value = normalize_text(f"{payload.get('texto') or ''}")
            is_private = bool(payload.get("esPrivado"))
        else:
            text_value = normalize_text(f"{payload or ''}")
            is_private = False

        if text_value:
            section_name = f"contenido:{column_id}"
            if is_private:
                section_name = f"{section_name}:privado"
            sections.append({"section": section_name, "text": text_value})

    return sections


def _fetch_biblioteca_rows(since: Optional[datetime]) -> List[Dict[str, Any]]:
    from app.utils.database import get_db_connection

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    base_query = (
        "SELECT id, casaMatrizId, categoriaId, nombre, descripcion, contenido, "
        "linkRepositorio, instruccionesInstalacion, instruccionesProd, manualUsuario, "
        "notasTecnicas, updatedAt "
        "FROM BibliotecaProyectos"
    )

    if since:
        query = base_query + " WHERE updatedAt >= %s ORDER BY updatedAt ASC"
        cursor.execute(query, (since,))
    else:
        query = base_query + " ORDER BY updatedAt ASC"
        cursor.execute(query)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def _build_chunks_for_project(
    row: Dict[str, Any],
    embedding_service,
    chunk_size: int,
    overlap: int,
) -> List[Dict[str, Any]]:
    project_id = int(row["id"])
    sections = _extract_sections(row)

    texts: List[str] = []
    chunk_payloads: List[Dict[str, Any]] = []
    chunk_index = 0

    for section in sections:
        section_chunks = chunk_text(
            section["text"], chunk_size=chunk_size, overlap=overlap
        )
        for piece in section_chunks:
            content_hash = hashlib.sha256(piece.encode("utf-8")).hexdigest()
            metadata = {
                "project_name": row.get("nombre"),
                "section": section["section"],
                "casa_matriz_id": row.get("casaMatrizId"),
                "categoria_id": row.get("categoriaId"),
                "updated_at": row.get("updatedAt").isoformat()
                if row.get("updatedAt")
                else None,
            }
            chunk_payloads.append(
                {
                    "source_type": SOURCE_TYPE,
                    "source_id": project_id,
                    "chunk_index": chunk_index,
                    "chunk_text": piece,
                    "metadata": metadata,
                    "content_hash": content_hash,
                }
            )
            texts.append(piece)
            chunk_index += 1

    embeddings = embedding_service.embed_documents(texts)
    for payload, embedding in zip(chunk_payloads, embeddings):
        payload["embedding"] = embedding

    return chunk_payloads


def run_ingest(
    full_reindex: bool, chunk_size: int = 900, overlap: int = 150
) -> Dict[str, Any]:
    from app.utils.embeddings import EmbeddingService
    from app.utils.vector_store import VectorStore

    vector_store = VectorStore()
    embedding_service = EmbeddingService()

    vector_store.ensure_schema()
    state = _load_state()

    since: Optional[datetime] = None
    if not full_reindex:
        since_raw = state.get("biblioteca_last_sync_at")
        if since_raw:
            try:
                since = datetime.fromisoformat(since_raw)
            except ValueError:
                since = None

    rows = _fetch_biblioteca_rows(since=since)

    processed_projects = 0
    stored_chunks = 0

    for row in rows:
        project_id = int(row["id"])
        chunks = _build_chunks_for_project(
            row=row,
            embedding_service=embedding_service,
            chunk_size=chunk_size,
            overlap=overlap,
        )
        vector_store.delete_source_chunks(SOURCE_TYPE, project_id)
        vector_store.upsert_chunks(chunks)

        processed_projects += 1
        stored_chunks += len(chunks)

    now_iso = datetime.now(timezone.utc).isoformat()
    state["biblioteca_last_sync_at"] = now_iso
    _save_state(state)

    result = {
        "processed_projects": processed_projects,
        "stored_chunks": stored_chunks,
        "full_reindex": full_reindex,
        "last_sync_at": now_iso,
    }
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Indexa BibliotecaProyectos en pgvector"
    )
    parser.add_argument(
        "--full-reindex", action="store_true", help="Reindexa todo desde cero"
    )
    parser.add_argument("--chunk-size", type=int, default=900)
    parser.add_argument("--overlap", type=int, default=150)
    args = parser.parse_args()

    result = run_ingest(
        full_reindex=args.full_reindex,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
    )
    print(json.dumps(result, ensure_ascii=True, indent=2), flush=True)


if __name__ == "__main__":
    main()
