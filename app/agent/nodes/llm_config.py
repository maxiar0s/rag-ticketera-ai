import os
from dataclasses import dataclass
from typing import Any, List

from app.agent.tools import ALL_TOOLS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI


def _is_retryable_error(error: Exception) -> bool:
    message = str(error).lower()
    retryable_signals = (
        "429",
        "rate limit",
        "quota",
        "too many requests",
        "overloaded",
        "timeout",
        "temporarily unavailable",
        "service unavailable",
        "connection error",
    )
    return any(signal in message for signal in retryable_signals)


@dataclass
class ProviderClient:
    provider: str
    client: Any


class FallbackLLM:
    def __init__(self, clients: List[ProviderClient]):
        if not clients:
            raise RuntimeError(
                "No hay proveedores configurados para LLM. "
                "Configura GOOGLE_API_KEY, OPENROUTER_API_KEY, NVIDIA_API_KEY o MISTRAL_API_KEY."
            )
        self.clients = clients
        self._cursor = 0

    def invoke(self, messages: Any) -> Any:
        errors: List[str] = []
        total = len(self.clients)

        for offset in range(total):
            idx = (self._cursor + offset) % total
            candidate = self.clients[idx]

            try:
                response = candidate.client.invoke(messages)
                self._cursor = idx
                print(f"✅ LLM provider activo: {candidate.provider}", flush=True)
                return response
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{candidate.provider}: {exc}")
                if _is_retryable_error(exc):
                    print(
                        f"⚠️  Fallback por error temporal en {candidate.provider}",
                        flush=True,
                    )
                else:
                    print(
                        f"⚠️  Error en {candidate.provider}, probando siguiente proveedor",
                        flush=True,
                    )

        raise RuntimeError(
            "Todos los proveedores LLM fallaron. Detalles: " + " | ".join(errors)
        )


class FallbackLLMFactory:
    def __init__(self):
        self.default_temperature = float(os.getenv("LLM_TEMPERATURE", "0"))

    @staticmethod
    def _get_tier_env(base_key: str, tier: str, default_value: str = "") -> str:
        tier_key = f"{base_key}_{tier.upper()}"
        value = os.getenv(tier_key)
        if value is not None and value.strip():
            return value.strip()

        fallback = os.getenv(base_key)
        if fallback is not None and fallback.strip():
            return fallback.strip()

        return default_value

    def _get_temperature(self, tier: str) -> float:
        raw_value = self._get_tier_env(
            "LLM_TEMPERATURE", tier, str(self.default_temperature)
        )
        try:
            return float(raw_value)
        except ValueError:
            return self.default_temperature

    def _build_provider_clients(self, tools: List[Any], tier: str) -> List[ProviderClient]:
        clients: List[ProviderClient] = []
        temperature = self._get_temperature(tier)

        provider_order = [
            item.strip().lower()
            for item in self._get_tier_env(
                "LLM_PROVIDER_ORDER", tier, "google,openrouter,nvidia,mistral"
            ).split(",")
            if item.strip()
        ]

        google_key = os.getenv("GOOGLE_API_KEY", "").strip()
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        nvidia_key = os.getenv("NVIDIA_API_KEY", "").strip()
        mistral_key = os.getenv("MISTRAL_API_KEY", "").strip()

        google_model = self._get_tier_env("GOOGLE_MODEL", tier, "gemma-3-27b-it")
        openrouter_model = self._get_tier_env(
            "OPENROUTER_MODEL", tier, "nvidia/nemotron-3-nano-30b-a3b:free"
        )
        nvidia_model = self._get_tier_env(
            "NVIDIA_MODEL", tier, "meta/llama-3.1-8b-instruct"
        )
        mistral_model = self._get_tier_env(
            "MISTRAL_MODEL", tier, "mistral-small-latest"
        )

        for provider in provider_order:
            if provider == "google" and google_key:
                client = ChatGoogleGenerativeAI(
                    model=google_model,
                    temperature=temperature,
                    google_api_key=google_key,
                ).bind_tools(tools)
                clients.append(ProviderClient("google", client))

            if provider == "openrouter" and openrouter_key:
                default_headers = {}
                if os.getenv("OPENROUTER_HTTP_REFERER"):
                    default_headers["HTTP-Referer"] = os.getenv(
                        "OPENROUTER_HTTP_REFERER", ""
                    )
                if os.getenv("OPENROUTER_X_TITLE"):
                    default_headers["X-Title"] = os.getenv("OPENROUTER_X_TITLE", "")

                client = ChatOpenAI(
                    model=openrouter_model,
                    temperature=temperature,
                    api_key=openrouter_key,
                    base_url="https://openrouter.ai/api/v1",
                    default_headers=default_headers or None,
                ).bind_tools(tools)
                clients.append(ProviderClient("openrouter", client))

            if provider == "nvidia" and nvidia_key:
                if "embed" in nvidia_model.lower():
                    print(
                        "⚠️  NVIDIA_MODEL parece de embeddings y no de chat/tool-calling: "
                        f"{nvidia_model}. Se omite proveedor nvidia.",
                        flush=True,
                    )
                    continue
                client = ChatOpenAI(
                    model=nvidia_model,
                    temperature=temperature,
                    api_key=nvidia_key,
                    base_url="https://integrate.api.nvidia.com/v1",
                ).bind_tools(tools)
                clients.append(ProviderClient("nvidia", client))

            if provider == "mistral" and mistral_key:
                client = ChatOpenAI(
                    model=mistral_model,
                    temperature=temperature,
                    api_key=mistral_key,
                    base_url="https://api.mistral.ai/v1",
                ).bind_tools(tools)
                clients.append(ProviderClient("mistral", client))

        return clients

    def bind_tools(self, tools: List[Any], tier: str = "medium") -> FallbackLLM:
        clients = self._build_provider_clients(tools, tier=tier)
        return FallbackLLM(clients)


class TieredLLMRouter:
    VALID_TIERS = {"low", "medium", "high"}

    def __init__(self, factory: FallbackLLMFactory, tools: List[Any]):
        self.factory = factory
        self.tools = tools
        self._tier_llms: dict[str, FallbackLLM] = {}

    def _normalize_tier(self, tier: str) -> str:
        normalized = (tier or "medium").strip().lower()
        if normalized not in self.VALID_TIERS:
            return "medium"
        return normalized

    def _get_llm(self, tier: str) -> FallbackLLM:
        normalized_tier = self._normalize_tier(tier)
        if normalized_tier not in self._tier_llms:
            self._tier_llms[normalized_tier] = self.factory.bind_tools(
                self.tools, tier=normalized_tier
            )
        return self._tier_llms[normalized_tier]

    def invoke(self, messages: Any, tier: str = "medium") -> Any:
        llm = self._get_llm(tier)
        print(f"🧭 LLM tier seleccionado: {self._normalize_tier(tier)}", flush=True)
        return llm.invoke(messages)


_factory = FallbackLLMFactory()
llm = _factory.bind_tools(ALL_TOOLS, tier="medium")
llm_router = TieredLLMRouter(_factory, ALL_TOOLS)
