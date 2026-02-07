"""
配置管理模块
/backend/config.py
"""
import os
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from enum import Enum

class LLMProvider(Enum):
    """
    LLM 服务提供商枚举
    """
    QWEN = "qwen"
    DS = "ds"

class LLMConfig(BaseModel):
    """大模型配置"""
    provider: str = "openai"
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4096


class Settings:
    """应用配置"""

    # 服务配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # CORS配置
    CORS_ORIGINS: list = ["*"]

    # LLM配置 - 从环境变量加载
    QWEN_LLM_PROVIDER: str = os.getenv("QWEN_LLM_PROVIDER", "openai")
    QWEN_LLM_BASE_URL: str = os.getenv("QWEN_LLM_BASE_URL", "https://api.openai.com/v1")
    QWEN_LLM_API_KEY: str = os.getenv("QWEN_LLM_API_KEY", "")
    QWEN_LLM_MODEL: str = os.getenv("QWEN_LLM_MODEL", "gpt-4o-mini")

    DS_LLM_PROVIDER: str = os.getenv("DS_LLM_PROVIDER", "openai")
    DS_LLM_BASE_URL: str = os.getenv("DS_LLM_BASE_URL", "https://api.openai.com/v1")
    DS_LLM_API_KEY: str = os.getenv("DS_LLM_API_KEY", "")
    DS_LLM_MODEL: str = os.getenv("DS_LLM_MODEL", "gpt-4o-mini")

    @classmethod
    def get_llm_config(cls, type:LLMProvider.QWEN, override: Optional[dict] = None) -> LLMConfig:
        """获取LLM配置，支持覆盖"""
        if type == LLMProvider.DS:
            config = LLMConfig(
                provider=cls.DS_LLM_PROVIDER,
                base_url=cls.DS_LLM_BASE_URL,
                api_key=cls.DS_LLM_API_KEY,
                model=cls.DS_LLM_MODEL
            )
        else:
            config = LLMConfig(
                provider=cls.QWEN_LLM_PROVIDER,
                base_url=cls.QWEN_LLM_BASE_URL,
                api_key=cls.QWEN_LLM_API_KEY,
                model=cls.QWEN_LLM_MODEL
            )
        if override:
            config = LLMConfig(**{**config.model_dump(), **override})
        return config


settings = Settings()