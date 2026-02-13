import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import psycopg


@dataclass
class VectorMatch:
    source_type: str
    source_id: int
    chunk_index: int
    chunk_text: str
    metadata: Dict[str, Any]
    score: float


def _vector_literal(values: List[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


class VectorStore:
    def __init__(self):
        self.host = os.getenv("POSTGRES_HOST", "localhost")
        self.port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.dbname = os.getenv("POSTGRES_DB", "rag_knowledge_base")
        self.user = os.getenv("POSTGRES_USER", "rag_user")
        self.password = os.getenv("POSTGRES_PASSWORD", "rag_password_dev")
        self.embed_dim = int(os.getenv("RAG_EMBED_DIM", "768"))

    def _connect(self):
        return psycopg.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            autocommit=True,
        )

    def ensure_schema(self):
        sql_path = Path(__file__).resolve().parent.parent / "sql" / "001_kb_chunks.sql"
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS kb_chunks (
                        id UUID PRIMARY KEY,
                        source_type VARCHAR(64) NOT NULL,
                        source_id BIGINT NOT NULL,
                        chunk_index INTEGER NOT NULL,
                        chunk_text TEXT NOT NULL,
                        embedding VECTOR({self.embed_dim}) NOT NULL,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        content_hash VARCHAR(64) NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        UNIQUE (source_type, source_id, chunk_index)
                    );
                    """
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_kb_chunks_source "
                    "ON kb_chunks (source_type, source_id);"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_kb_chunks_metadata "
                    "ON kb_chunks USING GIN (metadata);"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding_ivfflat "
                    "ON kb_chunks USING ivfflat (embedding vector_cosine_ops) "
                    "WITH (lists = 100);"
                )

        if sql_path.exists():
            print(f"📦 Schema verificado ({sql_path.name})", flush=True)

    def delete_source_chunks(self, source_type: str, source_id: int):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM kb_chunks WHERE source_type = %s AND source_id = %s",
                    (source_type, source_id),
                )

    def upsert_chunks(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            return

        with self._connect() as conn:
            with conn.cursor() as cur:
                for chunk in chunks:
                    cur.execute(
                        """
                        INSERT INTO kb_chunks (
                            id,
                            source_type,
                            source_id,
                            chunk_index,
                            chunk_text,
                            embedding,
                            metadata,
                            content_hash,
                            created_at,
                            updated_at
                        ) VALUES (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s::vector,
                            %s::jsonb,
                            %s,
                            NOW(),
                            NOW()
                        )
                        ON CONFLICT (source_type, source_id, chunk_index)
                        DO UPDATE SET
                            chunk_text = EXCLUDED.chunk_text,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata,
                            content_hash = EXCLUDED.content_hash,
                            updated_at = NOW();
                        """,
                        (
                            chunk.get("id") or str(uuid.uuid4()),
                            chunk["source_type"],
                            chunk["source_id"],
                            chunk["chunk_index"],
                            chunk["chunk_text"],
                            _vector_literal(chunk["embedding"]),
                            json.dumps(chunk.get("metadata", {}), ensure_ascii=True),
                            chunk["content_hash"],
                        ),
                    )

    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 8,
        min_score: float = 0.2,
    ) -> List[VectorMatch]:
        if not query_embedding:
            return []

        vector = _vector_literal(query_embedding)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        source_type,
                        source_id,
                        chunk_index,
                        chunk_text,
                        metadata,
                        1 - (embedding <=> %s::vector) AS score
                    FROM kb_chunks
                    WHERE 1 - (embedding <=> %s::vector) >= %s
                    ORDER BY embedding <=> %s::vector ASC
                    LIMIT %s;
                    """,
                    (vector, vector, min_score, vector, top_k),
                )
                rows = cur.fetchall()

        matches: List[VectorMatch] = []
        for row in rows:
            matches.append(
                VectorMatch(
                    source_type=row[0],
                    source_id=row[1],
                    chunk_index=row[2],
                    chunk_text=row[3],
                    metadata=row[4] or {},
                    score=float(row[5]),
                )
            )

        return matches
