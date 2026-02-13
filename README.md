# RAG Ticketera AI

Microservicio FastAPI con LangGraph para respuestas de soporte y consulta de tickets.

## Estructura de carpetas

- `app/agent/`: Orquestacion del agente (grafo, estado, tools, nodos).
- `app/infrastructure/`: Integraciones de infraestructura (MySQL, pgvector, embeddings).
- `app/indexing/`: Pipeline de indexacion y utilidades de chunking.
- `app/scripts/`: Entrypoints operativos (ej: reindex).
- `app/sql/`: Scripts SQL de schema.

## Fase 1 (RAG vectorial en pgvector)

Esta fase activa retrieval real sobre `pgvector` usando conocimiento de `BibliotecaProyectos`.

### Flujo

1. `retrieve_node` recibe la consulta del usuario.
2. Genera embedding del query (`Google text-embedding-004` por defecto).
3. Busca chunks similares en `kb_chunks` (Postgres + pgvector).
4. Envía contexto al nodo `generate`.
5. El modelo responde y la API devuelve `solution` + `sources`.

## Variables de entorno relevantes

- `RAG_VECTOR_ENABLED=true`
- `RAG_TOP_K=8`
- `RAG_SCORE_THRESHOLD=0.2`
- `RAG_EMBED_PROVIDER=google`
- `GOOGLE_API_KEY=<tu_key>`
- `GOOGLE_EMBEDDING_MODEL=models/text-embedding-004`
- `RAG_EMBED_DIM=768`

Postgres vectorial:

- `POSTGRES_HOST=vector-db`
- `POSTGRES_PORT=5432`
- `POSTGRES_USER=rag_user`
- `POSTGRES_PASSWORD=rag_password_dev`
- `POSTGRES_DB=rag_knowledge_base`

MySQL de negocio (fuente para indexar Biblioteca):

- `MYSQL_HOST=...`
- `MYSQL_PORT=...`
- `MYSQL_USER=...`
- `MYSQL_PASSWORD=...`
- `MYSQL_DB=...`

## Indexacion de conocimiento

Comando de reindex completo:

```bash
python -m app.scripts.reindex_kb --full-reindex
```

Comando incremental (desde ultimo sync):

```bash
python -m app.scripts.reindex_kb
```

Estado de sync incremental:

- `app/data/ingest_state.json`

## Esquema vectorial

Archivo:

- `app/sql/001_kb_chunks.sql`

Tabla principal:

- `kb_chunks`
  - `source_type`, `source_id`, `chunk_index`
  - `chunk_text`
  - `embedding`
  - `metadata`
  - `content_hash`

## Nota de seguridad

La ingesta excluye campos sensibles para no indexar secretos por defecto.
En esta fase no se indexan credenciales ni variables de entorno de proyectos.
