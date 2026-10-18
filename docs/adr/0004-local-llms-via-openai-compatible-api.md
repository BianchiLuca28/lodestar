# Local LLMs through an OpenAI-compatible endpoint, one model per task

All model calls go to a configurable OpenAI-compatible endpoint, Ollama by default, on the user's 16 GB GPU. Each task (parse, chat, vision, embed) has its own model in settings, so models can be swapped and compared on the eval set without code changes. Financial data never leaves the machine for inference; other users can point the same setting at LM Studio, vLLM or a hosted endpoint.
