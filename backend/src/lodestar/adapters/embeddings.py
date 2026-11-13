"""Text embedders: the configured OpenAI-compatible endpoint (invariant 4), and a fake for tests."""

import hashlib
import math
import re
from collections.abc import Sequence
from typing import Protocol

from langchain_openai import OpenAIEmbeddings


class Embedder(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class OpenAICompatEmbedder:
    """`models.embed` (bge-m3 by default) served by Ollama under /v1."""

    def __init__(self, base_url: str, model: str, timeout: float = 60) -> None:
        self._client = OpenAIEmbeddings(
            base_url=f"{base_url}/v1",
            model=model,
            api_key="ollama",  # type: ignore[arg-type]
            check_embedding_ctx_length=False,  # Ollama takes raw strings, not OpenAI token ids
            timeout=timeout,
            max_retries=0,
        )

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return self._client.embed_documents(list(texts))


class HashingEmbedder:
    """Deterministic character-trigram vectors: similar spellings land close. Tests and CI only."""

    def __init__(self, dimensions: int = 64) -> None:
        self.dimensions = dimensions

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._one(text) for text in texts]

    def _one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for word in re.findall(r"\w+", text.lower()):
            padded = f" {word} "
            for i in range(len(padded) - 2):
                digest = hashlib.blake2b(padded[i : i + 3].encode(), digest_size=4).digest()
                vector[int.from_bytes(digest, "little") % self.dimensions] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]
