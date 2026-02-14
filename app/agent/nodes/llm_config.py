import os
from dataclasses import dataclass
from typing import Any, List

from app.agent.tools import consultar_mis_tickets
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
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0"))

    def _build_provider_clients(self, tools: List[Any]) -> List[ProviderClient]:
        clients: List[ProviderClient] = []

        provider_order = [
            item.strip().lower()
            for item in os.getenv(
                "LLM_PROVIDER_ORDER", "google,openrouter,nvidia,mistral"
            ).split(",")
            if item.strip()
        ]

        google_key = os.getenv("GOOGLE_API_KEY", "").strip()
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        nvidia_key = os.getenv("NVIDIA_API_KEY", "").strip()
        mistral_key = os.getenv("MISTRAL_API_KEY", "").strip()

        google_model = os.getenv("GOOGLE_MODEL", "gemma-3-27b-it")
        openrouter_model = os.getenv(
            "OPENROUTER_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free"
        )
        nvidia_model = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")
        mistral_model = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

        for provider in provider_order:
            if provider == "google" and google_key:
                client = ChatGoogleGenerativeAI(
                    model=google_model,
                    temperature=self.temperature,
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
                    temperature=self.temperature,
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
                    temperature=self.temperature,
                    api_key=nvidia_key,
                    base_url="https://integrate.api.nvidia.com/v1",
                ).bind_tools(tools)
                clients.append(ProviderClient("nvidia", client))

            if provider == "mistral" and mistral_key:
                client = ChatOpenAI(
                    model=mistral_model,
                    temperature=self.temperature,
                    api_key=mistral_key,
                    base_url="https://api.mistral.ai/v1",
                ).bind_tools(tools)
                clients.append(ProviderClient("mistral", client))

        return clients

    def bind_tools(self, tools: List[Any]) -> FallbackLLM:
        clients = self._build_provider_clients(tools)
        return FallbackLLM(clients)


llm = FallbackLLMFactory().bind_tools([consultar_mis_tickets])
