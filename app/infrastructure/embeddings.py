import os
from typing import List

from langchain_google_genai import GoogleGenerativeAIEmbeddings


class EmbeddingService:
    def __init__(self):
        provider = os.getenv("RAG_EMBED_PROVIDER", "google").strip().lower()
        if provider != "google":
            raise RuntimeError(
                f"Proveedor de embeddings no soportado: {provider}. "
                "Use RAG_EMBED_PROVIDER=google."
            )

        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("Falta GOOGLE_API_KEY para embeddings.")

        model = os.getenv("GOOGLE_EMBEDDING_MODEL", "models/text-embedding-004").strip()
        self.client = GoogleGenerativeAIEmbeddings(model=model, google_api_key=api_key)

    def embed_query(self, text: str) -> List[float]:
        return self.client.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return self.client.embed_documents(texts)
