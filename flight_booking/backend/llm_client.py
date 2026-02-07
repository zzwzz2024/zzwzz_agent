"""
机票预订系统 - 大模型客户端
/flight_booking/llm_client.py
"""
import json
import httpx
from typing import AsyncGenerator, List, Dict, Any, Optional
from flight_booking.backend.config import LLMConfig, settings


class LLMClient:
    """大模型客户端 - 支持流式输出和函数调用"""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or settings.get_llm_config()

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }

    def _build_request_body(
            self,
            messages: List[Dict[str, str]],
            stream: bool = True,
            tools: Optional[List[Dict]] = None,
            **kwargs
    ) -> Dict[str, Any]:
        body = {
            "model": self.config.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": stream
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        return body

    async def chat_completion(
            self,
            messages: List[Dict[str, str]],
            tools: Optional[List[Dict]] = None,
            **kwargs
    ) -> str:
        """非流式对话"""
        url = f"{self.config.base_url}/chat/completions"
        body = self._build_request_body(messages, stream=False, tools=tools, **kwargs)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=self._get_headers(), json=body)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def stream_chat_completion(
            self,
            messages: List[Dict[str, str]],
            **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        url = f"{self.config.base_url}/chat/completions"
        body = self._build_request_body(messages, stream=True, **kwargs)

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=self._get_headers(), json=body) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue

                    data = line[5:].strip()
                    if data == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data)
                        content = chunk.get("choices", [{}])[0].get("delta", {}).get("content")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue


def get_llm_client(config: Optional[LLMConfig] = None) -> LLMClient:
    return LLMClient(config)
