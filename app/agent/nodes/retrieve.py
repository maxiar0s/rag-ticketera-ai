import os

from app.agent.state import AgentState
from app.infrastructure.embeddings import EmbeddingService
from app.infrastructure.vector_store import VectorStore


def _is_vector_enabled() -> bool:
    return os.getenv("RAG_VECTOR_ENABLED", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def retrieve_node(state: AgentState):
    print("--- 🔍 NODE: RETRIEVE ---", flush=True)
    if not state["messages"]:
        return {"documents": [], "sources": []}

    if not _is_vector_enabled():
        print("ℹ️  RAG_VECTOR_ENABLED=false, retrieval omitido", flush=True)
        return {"documents": [], "sources": []}

    query = state["messages"][-1].content
    top_k = int(os.getenv("RAG_TOP_K", "8"))
    min_score = float(os.getenv("RAG_SCORE_THRESHOLD", "0.2"))

    try:
        embed_service = EmbeddingService()
        vector_store = VectorStore()
        vector = embed_service.embed_query(query)
        matches = vector_store.similarity_search(
            vector, top_k=top_k, min_score=min_score
        )

        documents = []
        sources = []
        for match in matches:
            section = match.metadata.get("section", "general")
            project_name = match.metadata.get(
                "project_name", f"proyecto-{match.source_id}"
            )
            documents.append(
                (
                    f"[Fuente: {project_name} | seccion: {section} | "
                    f"score: {match.score:.3f}] {match.chunk_text}"
                )
            )
            sources.append(
                {
                    "source_type": match.source_type,
                    "source_id": match.source_id,
                    "chunk_index": match.chunk_index,
                    "section": section,
                    "project_name": project_name,
                    "score": round(match.score, 4),
                }
            )

        print(f"📚 Retrieval chunks: {len(documents)}", flush=True)
        return {"documents": documents, "sources": sources}
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️  Error en retrieval vectorial: {exc}", flush=True)
        return {"documents": [], "sources": []}
