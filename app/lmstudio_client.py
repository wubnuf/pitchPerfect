# app/lmstudio_client.py

import os
import requests

LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "local-model")
LM_STUDIO_API_KEY = os.getenv("LM_STUDIO_API_KEY", "lm-studio")


def chat_completion(
    messages: list,
    temperature: float = 0.7,
    max_tokens: int = 150,
    model: str = None,
) -> str:
    """Call LM Studio's OpenAI-compatible chat/completions endpoint.

    LM Studio exposes the same API shape as OpenAI, so this sends a standard
    chat completion request to the local server.

    Args:
        messages: List of {"role": ..., "content": ...} dicts.
        temperature: Sampling temperature.
        max_tokens: Max tokens to generate.
        model: Override model name (defaults to LM_STUDIO_MODEL env var).

    Returns:
        The assistant's reply as a string.
    """
    url = f"{LM_STUDIO_BASE_URL}/chat/completions"
    payload = {
        "model": model or LM_STUDIO_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LM_STUDIO_API_KEY}",
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def list_models() -> list:
    """List models currently loaded in LM Studio."""
    url = f"{LM_STUDIO_BASE_URL}/models"
    headers = {"Authorization": f"Bearer {LM_STUDIO_API_KEY}"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json().get("data", [])


def is_available() -> bool:
    """Check if LM Studio server is reachable."""
    try:
        url = f"{LM_STUDIO_BASE_URL}/models"
        headers = {"Authorization": f"Bearer {LM_STUDIO_API_KEY}"}
        resp = requests.get(url, headers=headers, timeout=5)
        return resp.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False
