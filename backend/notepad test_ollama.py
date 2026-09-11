import asyncio
import httpx


async def main():
    url = "http://localhost:11434/api/chat"

    payload = {
        "model": "llama3.2:latest",
        "messages": [
            {
                "role": "user",
                "content": "Reply only with OK",
            }
        ],
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            url,
            json=payload,
        )

        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)


asyncio.run(main())