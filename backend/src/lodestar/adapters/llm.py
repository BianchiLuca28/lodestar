"""The chat model behind every AI task: the configured OpenAI-compatible endpoint (invariant 4)."""

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI


def chat_model(base_url: str, model: str, timeout: float = 120) -> BaseChatModel:
    # Ollama serves the OpenAI API under /v1 and ignores the key; temperature 0 for extraction.
    return ChatOpenAI(
        base_url=f"{base_url}/v1",
        model=model,
        api_key="ollama",  # type: ignore[arg-type]
        temperature=0,
        timeout=timeout,
        max_retries=0,
    )
