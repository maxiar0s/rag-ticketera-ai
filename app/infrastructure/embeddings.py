import os
from dataclasses import dataclass
from typing import Any, List

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings


@dataclass
class EmbeddingCandidate:
    provider: str
    model: str
    client: Any


def _ordered_unique(items: List[str]) -> List[str]:
    seen: set[str] = set()
    result: List[str] = []
    for item in items:
        value = item.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _read_model_list(
    primary_env: str, fallback_env: str, default_model: str
) -> List[str]:
    primary = os.getenv(primary_env, default_model).strip()
    fallback_items = [
        item.strip() for item in os.getenv(fallback_env, "").split(",") if item.strip()
    ]
    return _ordered_unique([primary] + fallback_items)


class EmbeddingService:
    def __init__(self):
        self._cursor = 0
        self.candidates = self._build_candidates()
        if not self.candidates:
            raise RuntimeError(
                "No hay proveedores de embeddings configurados. "
                "Configura RAG_EMBED_PROVIDER=auto o un proveedor soportado "
                "(google/openrouter/nvidia/mistral) y su API key correspondiente."
            )

    def _build_candidates(self) -> List[EmbeddingCandidate]:
        selected_provider = os.getenv("RAG_EMBED_PROVIDER", "auto").strip().lower()
        if selected_provider not in {
            "auto",
            "google",
            "openrouter",
            "nvidia",
            "mistral",
        }:
            raise RuntimeError(
                f"Proveedor de embeddings no soportado: {selected_provider}. "
                "Use RAG_EMBED_PROVIDER=auto o uno de "
                "google/openrouter/nvidia/mistral."
            )

        provider_order = [
            item.strip().lower()
            for item in os.getenv(
                "RAG_EMBED_PROVIDER_ORDER", "google,openrouter,nvidia,mistral"
            ).split(",")
            if item.strip()
        ]

        if selected_provider != "auto":
            provider_order = [selected_provider]
        else:
            provider_order = _ordered_unique(provider_order)

        candidates: List[EmbeddingCandidate] = []
        for provider in provider_order:
            if provider == "google":
                candidates.extend(self._build_google_candidates())
            elif provider == "openrouter":
                candidates.extend(self._build_openrouter_candidates())
            elif provider == "nvidia":
                candidates.extend(self._build_nvidia_candidates())
            elif provider == "mistral":
                candidates.extend(self._build_mistral_candidates())
        return candidates

    def _build_google_candidates(self) -> List[EmbeddingCandidate]:
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        if not api_key:
            return []

        models = _read_model_list(
            "GOOGLE_EMBEDDING_MODEL",
            "GOOGLE_EMBEDDING_FALLBACKS",
            "models/text-embedding-004",
        )
        return [
            EmbeddingCandidate(
                provider="google",
                model=model,
                client=GoogleGenerativeAIEmbeddings(
                    model=model,
                    google_api_key=api_key,
                ),
            )
            for model in models
        ]

    def _build_openrouter_candidates(self) -> List[EmbeddingCandidate]:
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            return []

        models = _read_model_list(
            "OPENROUTER_EMBEDDING_MODEL",
            "OPENROUTER_EMBEDDING_FALLBACKS",
            "text-embedding-3-small",
        )

        default_headers = {}
        if os.getenv("OPENROUTER_HTTP_REFERER"):
            default_headers["HTTP-Referer"] = os.getenv("OPENROUTER_HTTP_REFERER", "")
        if os.getenv("OPENROUTER_X_TITLE"):
            default_headers["X-Title"] = os.getenv("OPENROUTER_X_TITLE", "")

        return [
            EmbeddingCandidate(
                provider="openrouter",
                model=model,
                client=OpenAIEmbeddings(
                    model=model,
                    api_key=api_key,
                    base_url="https://openrouter.ai/api/v1",
                    default_headers=default_headers or None,
                ),
            )
            for model in models
        ]

    def _build_nvidia_candidates(self) -> List[EmbeddingCandidate]:
        api_key = os.getenv("NVIDIA_API_KEY", "").strip()
        if not api_key:
            return []

        models = _read_model_list(
            "NVIDIA_EMBEDDING_MODEL",
            "NVIDIA_EMBEDDING_FALLBACKS",
            "nvidia/nv-embedqa-e5-v5",
        )
        return [
            EmbeddingCandidate(
                provider="nvidia",
                model=model,
                client=OpenAIEmbeddings(
                    model=model,
                    api_key=api_key,
                    base_url="https://integrate.api.nvidia.com/v1",
                ),
            )
            for model in models
        ]

    def _build_mistral_candidates(self) -> List[EmbeddingCandidate]:
        api_key = os.getenv("MISTRAL_API_KEY", "").strip()
        if not api_key:
            return []

        models = _read_model_list(
            "MISTRAL_EMBEDDING_MODEL",
            "MISTRAL_EMBEDDING_FALLBACKS",
            "mistral-embed",
        )
        return [
            EmbeddingCandidate(
                provider="mistral",
                model=model,
                client=OpenAIEmbeddings(
                    model=model,
                    api_key=api_key,
                    base_url="https://api.mistral.ai/v1",
                ),
            )
            for model in models
        ]

    def _run_with_fallback(self, action: str, payload: Any) -> Any:
        errors: List[str] = []
        total = len(self.candidates)

        for offset in range(total):
            idx = (self._cursor + offset) % total
            candidate = self.candidates[idx]
            try:
                if action == "query":
                    result = candidate.client.embed_query(payload)
                else:
                    result = candidate.client.embed_documents(payload)
                self._cursor = idx
                return result
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{candidate.provider}:{candidate.model} -> {exc}")
                print(
                    "⚠️  Embeddings fallback: "
                    f"fallo {candidate.provider}/{candidate.model}. "
                    "Probando siguiente proveedor/modelo...",
                    flush=True,
                )

        raise RuntimeError(
            "No se encontró un proveedor/modelo de embeddings válido. "
            "Configura un modelo soportado para tu cuenta en GOOGLE_/OPENROUTER_/"
            "NVIDIA_/MISTRAL_EMBEDDING_MODEL. "
            "Detalles: " + " | ".join(errors)
        )

    def embed_query(self, text: str) -> List[float]:
        return self._run_with_fallback("query", text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return self._run_with_fallback("documents", texts)
