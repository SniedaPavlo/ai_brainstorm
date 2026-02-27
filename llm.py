import requests
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, DEFAULT_MODEL


def chat(prompt: str, role_system: str = "", model: str = DEFAULT_MODEL) -> str:
    """Отправляет запрос к OpenRouter API."""
    messages = []
    if role_system:
        messages.append({"role": "system", "content": role_system})
    messages.append({"role": "user", "content": prompt})

    resp = requests.post(
        OPENROUTER_BASE_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={"model": model, "messages": messages},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]