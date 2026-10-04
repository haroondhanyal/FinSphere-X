"""Optional OpenAI Responses API client used by the Phase 10 assistance routes."""

import base64
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException

from app.core.config import settings


def provider_enabled() -> bool:
    return bool(settings.openai_api_key.strip())


def generate_text(instructions: str, source: str, *, max_output_tokens: int = 500) -> str | None:
    """Return model output, or None when AI is not configured.

    Source content and the API key never enter application logs. API errors are
    deliberately returned without provider response bodies, which can echo input.
    """
    if not provider_enabled():
        return None

    return _send_response(
        {
            "model": settings.openai_model,
            "instructions": instructions,
            "input": source,
            "max_output_tokens": max_output_tokens,
        }
    )


def generate_file_text(
    document_type: str,
    filename: str,
    mime_type: str,
    contents: bytes,
    *,
    max_output_tokens: int = 500,
) -> str | None:
    """Send an in-memory PDF or image directly as a Responses API input."""
    if not provider_enabled():
        return None
    encoded = base64.b64encode(contents).decode("ascii")
    if mime_type == "application/pdf":
        file_content = {
            "type": "input_file",
            "filename": filename,
            "file_data": f"data:{mime_type};base64,{encoded}",
            "detail": "high",
        }
    else:
        file_content = {
            "type": "input_image",
            "image_url": f"data:{mime_type};base64,{encoded}",
            "detail": "high",
        }
    return _send_response(
        {
            "model": settings.openai_model,
            "instructions": instructions,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": f"Extract dates and monetary amounts from this {document_type}. Return only a JSON object with string arrays amount_candidates and date_candidates. Do not infer missing values."},
                        file_content,
                    ],
                }
            ],
            "max_output_tokens": max_output_tokens,
        }
    )


def _send_response(payload: dict) -> str:
    # Keep these requests stateless; do not persist Responses API conversation state.
    payload["store"] = False
    payload = json.dumps(payload).encode("utf-8")
    request = Request(
        "https://api.openai.com/v1/responses",
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings.openai_timeout_seconds) as response:
            result = json.loads(response.read())
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="AI provider is temporarily unavailable. Please retry later.",
        ) from exc

    output = result.get("output_text")
    if not isinstance(output, str) or not output.strip():
        # Responses can contain several output items; collect only text content.
        chunks = []
        for item in result.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                    chunks.append(content["text"])
        output = "\n".join(chunks)
    if not output.strip():
        raise HTTPException(status_code=503, detail="AI provider returned no usable text.")
    return output.strip()
