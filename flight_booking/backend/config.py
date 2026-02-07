"""
机票预订系统 - 配置管理模块
/flight_booking/config.py
"""
import os
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


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
    PORT: int = int(os.getenv("PORT", 8001))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # CORS配置
    CORS_ORIGINS: list = ["*"]

    # LLM配置
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

    @classmethod
    def get_llm_config(cls, override: Optional[dict] = None) -> LLMConfig:
        """获取LLM配置"""
        config = LLMConfig(
            provider=cls.LLM_PROVIDER,
            base_url=cls.LLM_BASE_URL,
            api_key=cls.LLM_API_KEY,
            model=cls.LLM_MODEL
        )
        if override:
            config = LLMConfig(**{**config.model_dump(), **override})
        return config


settings = Settings()
