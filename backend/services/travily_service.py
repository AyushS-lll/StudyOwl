"""
Tavily search service — fetch related learning resources for a stuck student.
"""

import httpx
import json
import logging
from config import settings

logger = logging.getLogger(__name__)


async def fetch_learning_resource(question: str) -> dict[str, str] | None:
    """
    Query the Travily API for a learning article related to the student's question.

    Returns a dict with keys 'title', 'url', and 'summary', or None if the API is unavailable or fails.
    """
    resources = await fetch_learning_resources(question, limit=1)
    return resources[0] if resources else None


async def fetch_learning_resources(question: str, limit: int = 5) -> list[dict[str, str]]:
    """
    Query the Tavily API for multiple learning resources related to the student's question.

    Args:
        question: The student's homework question.
        limit: Number of results to fetch (default 5).

    Returns:
        List of dicts with keys 'title', 'url', and 'summary'.
        Returns empty list if the API is unavailable or fails.
    """
    if not settings.travily_api_url:
        logger.warning("Tavily API URL not configured")
        return []

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    if settings.travily_api_key:
        headers["Authorization"] = f"Bearer {settings.travily_api_key}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            logger.info(f"Calling Tavily search API with query: {question}")
            response = await client.post(
                settings.travily_api_url,
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": "1",
                    "method": "tools/call",
                    "params": {
                        "name": "tavily_search",
                        "arguments": {
                            "query": question,
                            "max_results": limit,
                            "search_depth": "basic"
                        }
                    }
                }
            )
            response.raise_for_status()
            
            # Parse Server-Sent Events (SSE) response
            payload = _parse_sse_response(response.text)
            logger.info(f"Tavily API response: {payload}")
    except Exception as e:
        logger.error(f"Tavily API error: {e}", exc_info=True)
        return []

    if not isinstance(payload, dict) or "result" not in payload:
        logger.warning(f"Unexpected Tavily response structure: {payload}")
        return []

    result = payload.get("result", {})
    
    # Extract resources from search results (nested in structuredContent)
    structured_content = result.get("structuredContent", {})
    results = structured_content.get("results", [])
    
    if not results:
        logger.warning(f"No results found in Tavily response")
        return []
    
    resources = []
    for item in results:
        if isinstance(item, dict):
            resource = {
                "title": item.get("title", "Learning Resource"),
                "url": item.get("url", ""),
                "summary": item.get("content", "")
            }
            if resource["title"] or resource["summary"]:
                resources.append(resource)
    
    logger.info(f"Extracted {len(resources)} resources from Tavily search")
    return resources


def _parse_sse_response(text: str) -> dict:
    """
    Parse Server-Sent Events response from Tavily API.
    
    Example format:
        event: message
        data: {"jsonrpc":"2.0","id":"1","result":{...}}
    """
    lines = text.strip().split('\n')
    for line in lines:
        if line.startswith("data: "):
            try:
                return json.loads(line[6:])  # Remove "data: " prefix
            except json.JSONDecodeError:
                logger.error(f"Failed to parse SSE data: {line}")
                return {}
    return {}
