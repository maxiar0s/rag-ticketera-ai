import re
from typing import List


def normalize_text(value: str) -> str:
    if not value:
        return ""
    text = value.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    clean_text = normalize_text(text)
    if not clean_text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size debe ser mayor a 0")
    if overlap < 0:
        raise ValueError("overlap no puede ser negativo")
    if overlap >= chunk_size:
        raise ValueError("overlap debe ser menor a chunk_size")

    chunks: List[str] = []
    start = 0
    text_length = len(clean_text)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        if end < text_length:
            next_break = clean_text.rfind(" ", start, end)
            if next_break > start + 100:
                end = next_break

        candidate = clean_text[start:end].strip()
        if candidate:
            chunks.append(candidate)

        if end >= text_length:
            break

        start = max(0, end - overlap)

    return chunks
