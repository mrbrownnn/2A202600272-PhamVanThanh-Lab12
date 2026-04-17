"""Authentication helpers for API key based access control."""

from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Validate X-API-Key header against configured secrets."""
    valid_keys = {settings.agent_api_key.strip()}
    if settings.openai_api_key:
        # Compatibility fallback: allow OpenAI key if AGENT key was not synchronized.
        valid_keys.add(settings.openai_api_key.strip())

    if not api_key or api_key.strip() not in valid_keys:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Include header: X-API-Key: <key>",
        )
    return api_key.strip()
