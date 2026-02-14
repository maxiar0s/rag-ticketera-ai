# RAG Phase 1 - Documentacion tecnica

## Objetivo

Reemplazar el retriever mock por retrieval semantico real usando PostgreSQL + pgvector.

## Componentes agregados

- `app/infrastructure/vector_store.py`
  - Conexion a Postgres vectorial.
  - Creacion/verificacion de schema `kb_chunks`.
  - `similarity_search` por cosine distance.
  - `upsert_chunks` para carga de conocimiento.

- `app/infrastructure/embeddings.py`
  - Wrapper de embeddings con `GoogleGenerativeAIEmbeddings`.

- `app/indexing/chunker.py`
  - Normalizacion de texto.
  - Segmentacion con overlap para mejorar recall.

- `app/indexing/ingest_biblioteca.py`
  - Lectura de `BibliotecaProyectos` desde MySQL.
  - Extraccion por secciones.
  - Embedding + escritura en `kb_chunks`.
  - Soporte full-reindex e incremental.

- `app/scripts/reindex_kb.py`
  - Entry point CLI para indexar.

## Cambios en flujo del agente

- `app/agent/nodes/retrieve.py`
  - Ahora consulta pgvector.
  - Respeta flags (`RAG_VECTOR_ENABLED`, `RAG_TOP_K`, `RAG_SCORE_THRESHOLD`).
  - Devuelve:
    - `documents`: contexto textual para el LLM.
    - `sources`: referencias estructuradas con score.

- `app/main.py`
  - Inicializa/verifica schema vectorial en startup.
  - Responde `sources` desde el estado del grafo.

- `app/agent/state.py`
  - Se agrega campo `sources` al estado.

## Campos indexados de Biblioteca

Se indexan por defecto:

- `nombre`
- `descripcion`
- `instruccionesInstalacion`
- `instruccionesProd`
- `manualUsuario`
- `notasTecnicas`
- `linkRepositorio`
- `contenido` (JSON dinamico por columnas)

No se indexan secretos de forma explicita:

- `credenciales`
- `envVariables`

## Ejecucion

Full reindex:

```bash
python -m app.scripts.reindex_kb --full-reindex
```

Incremental:

```bash
python -m app.scripts.reindex_kb
```

## Troubleshooting

- `No se pudo verificar schema vectorial`:
  - Revisar `POSTGRES_*` y conectividad Docker (`vector-db`).

- `Falta GOOGLE_API_KEY para embeddings`:
  - Definir `GOOGLE_API_KEY` en `.env` del backend RAG.

- `404 NOT_FOUND` en embedding model:
  - Definir `GOOGLE_EMBEDDING_MODEL=models/embedding-001`.
  - Opcional: configurar `GOOGLE_EMBEDDING_FALLBACKS` para fallback automático.

- `Retrieval chunks: 0`:
  - Ejecutar `--full-reindex`.
  - Revisar `RAG_SCORE_THRESHOLD` (bajarlo temporalmente a `0.1`).

- Respuestas sin fuentes:
  - Verificar que `RAG_VECTOR_ENABLED=true`.
  - Confirmar que `kb_chunks` tenga datos.
