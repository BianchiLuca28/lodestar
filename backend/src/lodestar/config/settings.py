import os
from dataclasses import dataclass

DEFAULT_LLM_BASE_URL = "http://127.0.0.1:11434"


@dataclass(frozen=True)
class Settings:
    """Runtime settings. Read from the environment until settings.yaml arrives in v0.1."""

    llm_base_url: str = DEFAULT_LLM_BASE_URL

    @classmethod
    def from_env(cls) -> "Settings":
        base_url = os.environ.get("LODESTAR_LLM_BASE_URL", DEFAULT_LLM_BASE_URL)
        return cls(llm_base_url=base_url.rstrip("/"))
