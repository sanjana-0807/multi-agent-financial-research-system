import os
from typing import Any

import httpx

from dotenv import load_dotenv


load_dotenv()


TAVILY_SEARCH_URL = (
    "https://api.tavily.com/search"
)


async def search_web(
    query: str,
    max_results: int = 5,
) -> list[dict[str, Any]]:

    if not query or not query.strip():

        return []

    api_key = os.getenv(
        "TAVILY_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "TAVILY_API_KEY is not configured."
        )

    max_results = max(
        1,
        min(max_results, 10),
    )

    payload = {

        "api_key": api_key,

        "query": query.strip(),

        "search_depth": "basic",

        "topic": "general",

        "max_results": max_results,

        "include_answer": False,

        "include_raw_content": False,
    }

    async with httpx.AsyncClient(
        timeout=15.0
    ) as client:

        response = await client.post(
            TAVILY_SEARCH_URL,
            json=payload,
        )

        response.raise_for_status()

    data = response.json()

    results = []

    for item in data.get(
        "results",
        [],
    ):

        results.append(
            {
                "title": item.get(
                    "title"
                ),

                "url": item.get(
                    "url"
                ),

                "content": item.get(
                    "content"
                ),
            }
        )

    return results