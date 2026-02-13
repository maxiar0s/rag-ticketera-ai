# AGENTS.md

Operational guidance for coding agents working in `rag-ticketera-ai`.

## 1) Project summary
- Language: Python 3.11
- API: FastAPI
- Agent orchestration: LangGraph + LangChain
- Stores: MySQL (business/source data), PostgreSQL + pgvector (RAG chunks)
- Packaging: `requirements.txt` (no `pyproject.toml`)
- CI workflow: `.github/workflows/ci.yml`

## 2) Key paths
- `app/main.py`: FastAPI app, auth, `/agent/process`, startup schema check
- `app/agent/graph.py`: graph wiring (`retriever -> generator -> tools -> generator`)
- `app/agent/state.py`: `AgentState` contract
- `app/agent/nodes/`: retrieval + generation nodes and LLM fallback config
- `app/agent/tools.py`: tool definitions (`consultar_mis_tickets`)
- `app/infrastructure/`: MySQL, embeddings, vector store adapters
- `app/indexing/`: chunking and Biblioteca ingestion pipeline
- `app/scripts/reindex_kb.py`: indexing CLI entrypoint
- `app/sql/001_kb_chunks.sql`: pgvector schema reference

## 3) Setup
```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```
Optional tools (used in CI/dev):
```bash
pip install pytest httpx flake8
```
Core env vars:
- Auth: `RAG_API_KEY`
- Retrieval: `RAG_VECTOR_ENABLED`, `RAG_TOP_K`, `RAG_SCORE_THRESHOLD`
- Embeddings: `RAG_EMBED_PROVIDER`, `RAG_EMBED_PROVIDER_ORDER`, provider API keys
- LLM fallback: `LLM_PROVIDER_ORDER`, provider model/env vars + API keys
- Postgres: `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- MySQL: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`

## 4) Build, run, lint, test
Run API locally:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Run with Docker Compose:
```bash
docker compose up --build
```
Indexing:
```bash
python -m app.scripts.reindex_kb --full-reindex
python -m app.scripts.reindex_kb
```
Lint (CI-equivalent):
```bash
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```
Notes:
- CI currently enforces only syntax/runtime-critical flake8 checks.
- No formatter config is present (no Black/Ruff/isort config).
Tests (important):
- Current state: no committed `tests/` suite; CI test step is placeholder.
- Default when tests exist: `pytest`
- Single test file: `pytest tests/test_file.py`
- Single test function: `pytest tests/test_file.py::test_specific_case`
- Single class method: `pytest tests/test_file.py::TestSuite::test_method`
- Pattern filter: `pytest -k "keyword"`
- Helpful smoke script: `python reproduce_issue.py`

## 5) Code style guidelines
### Imports
- Keep grouped order used in codebase:
  1) stdlib
  2) third-party
  3) local `app.*`
- Separate groups with a single blank line.
- Prefer explicit imports; avoid wildcard imports.
### Formatting and structure
- Follow existing PEP 8-like formatting and line wrapping.
- Prefer short, single-purpose functions.
- Use multiline call formatting for long argument lists.
- Keep SQL in readable multiline strings when non-trivial.
### Type hints
- Add hints for new public functions and return values.
- Keep consistency with existing patterns:
  - `TypedDict` for graph state (`AgentState`)
  - `@dataclass` for transport/config objects (`VectorMatch`, provider candidates)
- Prefer concrete containers in signatures when matching existing files (`List[...]`, `Dict[...]`).
### Naming
- Functions, variables, modules: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Favor domain-specific names (example: `similarity_search`, `run_ingest`).
### Error handling
- Use guard clauses for invalid or empty inputs.
- Wrap external I/O (DB/providers) in `try/except` and fail gracefully.
- Broad catches (`except Exception`) exist in this repo; if used, include actionable context.
- Prefer narrower exception types where practical.
- Always close DB cursors/connections (context manager or `finally`).
- Keep fallback behavior deterministic (provider order + cursor rotation).
### Logging and output
- Current convention is `print(..., flush=True)` for operational paths.
- Keep messages concise and useful for debugging fallbacks/retries.
- Avoid noisy debug logs unless they help diagnose provider or DB issues.
### API and graph contracts
- Preserve `AgentState` keys expected by nodes: `messages`, `documents`, `sources`, `final_response`.
- Do not rename graph node ids (`retriever`, `generator`, `tools`) unless wiring is updated too.
- Keep `/agent/process` response contract stable: `solution`, `sources`.
### Security and data handling
- Never hardcode real credentials.
- Use env vars for all secret/config values.
- Do not commit `.env` files.
- Keep ingestion conservative around sensitive fields.

## 6) Cursor/Copilot instructions status
Checked:
- `.cursor/rules/`
- `.cursorrules`
- `.github/copilot-instructions.md`
Current repository status:
- No Cursor rules detected.
- No Copilot instructions file detected.
If these files are later added, treat them as high-priority repository rules and merge guidance into this file.

## 7) Agent completion checklist
- Run CI-equivalent lint before finishing.
- Run the smallest relevant test selection when tests exist.
- For retrieval/indexing changes, validate env-driven behavior and fallback paths.
- Preserve backward compatibility of API/graph contracts unless explicitly requested.
- Update `AGENTS.md` when workflow, tooling, or conventions change.

## 8) Practical guardrails for agents
- Prefer minimal, targeted edits over large refactors.
- Do not rename public API fields without explicit request.
- Keep env-driven defaults stable unless asked to change behavior.
- For DB access code, maintain deterministic query ordering when possible.
- For provider fallback code, preserve provider order and cursor semantics.
- Keep operational prints concise; include provider/source context on failures.
- Avoid introducing new dependencies unless clearly required.
- If adding tests, prioritize unit tests around retrieval, tools, and API contracts.
- If docs or commands change, update this file and `README.md` together.

### Skills Registry

Auto-generated from `./.agents/skills` (repo) and `~/.agents/skills` (global).

| Skill | Source | Description |
|-------|--------|-------------|
| `agents-gemini-sync` | global | Sync `AGENTS.md` and `GEMINI.md` skill registry sections from both repository-local skills (`./.agents/skills`) and global skills (`~/.agents/skills`). Use when creating, renaming, deleting, or updating skills and you need agent docs to reflect current available skills. |
| `error-handling-patterns` | global | Master error handling patterns across languages including exceptions, Result types, error propagation, and graceful degradation to build resilient applications. Use when implementing error handling, designing APIs, or improving application reliability. |
| `find-skills` | global | Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill. |
| `frontend-design` | global | Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, artifacts, posters, or applications (examples include websites, landing pages, dashboards, React components, HTML/CSS layouts, or when styling/beautifying any web UI). Generates creative, polished code and UI design that avoids generic AI aesthetics. |
| `php-pro` | global | Use when building PHP applications with modern PHP 8.3+ features, Laravel, or Symfony frameworks. Invoke for strict typing, PHPStan level 9, async patterns with Swoole, PSR standards. |
| `skill-creator` | global | Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Claude's capabilities with specialized knowledge, workflows, or tool integrations. |
| `skill-sync` | global | Syncs skill metadata to AGENTS.md Auto-invoke sections. Trigger: When updating skill metadata (metadata.scope/metadata.auto_invoke), regenerating Auto-invoke tables, or running ./skills/skill-sync/assets/sync.sh (including --dry-run/--scope). |
### Auto-invoke Skills

When performing these actions, ALWAYS invoke the corresponding skill FIRST:

| Action | Skill |
|--------|-------|
| After creating/modifying a skill | `skill-sync` |
| Regenerate AGENTS.md Auto-invoke tables (sync.sh) | `skill-sync` |
| Troubleshoot why a skill is missing from AGENTS.md auto-invoke | `skill-sync` |

