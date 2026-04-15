"""
Travily service — fetch a related learning resource for a stuck student.
"""

import httpx
from config import settings


async def fetch_learning_resource(question: str) -> dict[str, str] | None:
    """
    Query the Travily API for a learning article related to the student's question.

    Returns a dict with keys 'title', 'url', and 'summary', or None if the API is unavailable or fails.
    """
    if not settings.travily_api_url:
        return None

    headers = {"Content-Type": "application/json"}
    if settings.travily_api_key:
        headers["Authorization"] = f"Bearer {settings.travily_api_key}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.travily_api_url,
                headers=headers,
                json={"query": question, "limit": 1},
            )
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return None

    if not isinstance(payload, dict):
        return None

    def extract_resource_from_object(obj: dict) -> dict[str, str] | None:
        title = obj.get("title") or obj.get("name") or obj.get("headline") or "Related resource"
        url = (
            obj.get("url")
            or obj.get("link")
            or obj.get("href")
            or obj.get("web_url")
            or obj.get("uri")
        )
        summary = (
            obj.get("summary")
            or obj.get("description")
            or obj.get("snippet")
            or obj.get("text")
            or obj.get("content")
        )
        if title or summary:
            return {"title": title, "url": url or "", "summary": summary or ""}
        return None

    # Attempt to extract a useful article from common response shapes.
    items = None
    for key in ("items", "results", "articles", "data", "links"):
        if key in payload and isinstance(payload[key], list) and payload[key]:
            items = payload[key]
            break

    if items:
        first = items[0]
        if isinstance(first, dict):
            resource = extract_resource_from_object(first)
            if resource:
                return resource
        return None

    resource = extract_resource_from_object(payload)
    if resource:
        return resource

    if "text" in payload and isinstance(payload["text"], str):
        return {"title": "Related resource", "url": "", "summary": payload["text"]}

    return None
