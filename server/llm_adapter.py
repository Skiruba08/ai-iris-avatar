import asyncio
import logging
from typing import Optional, Dict, Any

import aiohttp


class HttpLLMClient:
    def __init__(
        self,
        api_url: str,
        api_key: Optional[str] = None,
        system_message: Optional[str] = None,
        timeout: int = 60,
    ):
        self.api_url = api_url
        self.api_key = api_key
        self.system_message = system_message
        self.timeout = timeout

    async def generate(
        self,
        model: str,
        prompt: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        options = options or {}

        messages = []
        if self.system_message:
            messages.append({"role": "system", "content": self.system_message})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "user": "iris-server",
            "temperature": options.get("temperature", 0.7),
            "top_p": options.get("top_p", 0.9),
        }

        print("API URL:", self.api_url)
        print("MODEL:", model)
        print("API KEY PRESENT:", bool(self.api_key))
        print("AUTH HEADER:", "present" if headers.get("Authorization") else "missing")
        print("PAYLOAD:", payload)

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                ) as resp:
                    text = await resp.text()

                    if resp.status != 200:
                        logging.error("LLM API returned status %s: %s", resp.status, text)
                        return {"response": ""}

                    try:
                        j = await resp.json()
                    except Exception:
                        logging.exception("Failed to decode JSON from LLM API")
                        logging.error("Raw response text: %s", text)
                        return {"response": ""}

                    return {
                        "response": j.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    }

        except asyncio.TimeoutError:
            logging.exception("Timeout when calling LLM API")
            return {"response": ""}

        except Exception:
            logging.exception("Error when calling LLM API")
            return {"response": ""}