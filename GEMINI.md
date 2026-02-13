# GEMINI.md

Operational guidance for Gemini-based coding agents working in `rag-ticketera-ai`.

## Project Overview
- Python 3.11 FastAPI service with LangGraph/LangChain orchestration.
- Uses MySQL for business/source data and PostgreSQL + pgvector for RAG chunks.
- Main API entrypoint: `app/main.py`.

## Agent Expectations
- Keep API contracts stable unless explicitly asked to change them.
- Prefer minimal, targeted edits over broad refactors.
- Preserve deterministic fallback/provider ordering behavior.
- Avoid introducing new dependencies unless clearly necessary.

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
| `skill-sync` | global | Syncs skill metadata to AGENTS.md Auto-invoke sections. Trigger: When updating skill metadata (metadata.scope/metadata.auto_invoke), regenerating Auto-invoke tables, or running ./skills/skill-sync/assets/sync.sh (including --dry-run/--scope). |## Build, Lint, and Test Commands
- Install deps: `pip install -r requirements.txt`
- Run API: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- Lint: `flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics`
- Run tests (when present): `pytest`
- Single test file: `pytest tests/test_file.py`
- Single test: `pytest tests/test_file.py::test_specific_case`
- Single class method: `pytest tests/test_file.py::TestSuite::test_method`
