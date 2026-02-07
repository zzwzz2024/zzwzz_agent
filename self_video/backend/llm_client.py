"""
大模型客户端模块
/backend/llm_client.py
"""
import json
import httpx
from typing import AsyncGenerator, List, Dict, Any, Optional
from self_video.backend.config import LLMConfig, settings, LLMProvider


class LLMClient:
    """大模型客户端 - 支持流式输出"""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.qwen_llm_config = config or settings.get_llm_config(type=LLMProvider.DS)

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.qwen_llm_config.api_key}"
        }

    def _build_request_body(
            self,
            messages: List[Dict[str, str]],
            stream: bool = True,
            **kwargs
    ) -> Dict[str, Any]:
        """构建请求体"""
        return {
            "model": self.qwen_llm_config.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.qwen_llm_config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.qwen_llm_config.max_tokens),
            "stream": stream
        }

    async def chat_completion(
            self,
            messages: List[Dict[str, str]],
            **kwargs
    ) -> str:
        """非流式对话补全"""
        url = f"{self.qwen_llm_config.base_url}/chat/completions"
        body = self._build_request_body(messages, stream=False, **kwargs)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=body
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def stream_chat_completion(
            self,
            messages: List[Dict[str, str]],
            **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式对话补全 - 异步生成器"""
        url = f"{self.qwen_llm_config.base_url}/chat/completions"
        body = self._build_request_body(messages, stream=True, **kwargs)

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                    "POST",
                    url,
                    headers=self._get_headers(),
                    json=body
            ) as response:
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


# 全局客户端实例
def get_llm_client(config: Optional[LLMConfig] = None) -> LLMClient:
    """获取LLM客户端实例"""
    return LLMClient(config)