import httpx

PROBE_TIMEOUT_SECONDS = 2.0


async def llm_reachable(base_url: str) -> bool:
    """True when the OpenAI-compatible endpoint answers GET /v1/models with a 2xx."""
    try:
        async with httpx.AsyncClient(timeout=PROBE_TIMEOUT_SECONDS) as client:
            response = await client.get(f"{base_url}/v1/models")
    except httpx.HTTPError:
        return False
    return response.is_success
