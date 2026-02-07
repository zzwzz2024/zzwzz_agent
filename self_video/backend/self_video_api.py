"""
FastAPI 主入口
/backend/main.py
"""
import json
import asyncio
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from self_video.backend.config import settings, LLMConfig, LLMProvider
from self_video.backend.definitions import skill_registry
from self_video.backend.engine import create_workflow_engine, WorkflowEngine
from self_video.backend.llm_client import get_llm_client


# ============ 请求/响应模型 ============

class WorkflowRequest(BaseModel):
    """工作流请求"""
    topic: str
    config: Optional[dict] = None


class SkillExecuteRequest(BaseModel):
    """单个Skill执行请求"""
    skill_id: str
    topic: str
    context: dict = {}
    config: Optional[dict] = None


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    provider: str = "openai"
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4096


# ============ 应用初始化 ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    print("🚀 Agent Skills Backend Starting...")
    print(f"📍 Server: http://{settings.HOST}:{settings.PORT}")
    print(f"🤖 LLM Provider: {settings.QWEN_LLM_PROVIDER}")
    print(f"📦 Registered Skills: {[s.id for s in skill_registry.get_all()]}")
    yield
    print("👋 Agent Skills Backend Shutting down...")


app = FastAPI(
    title="Agent Skills API",
    description="公众号文章发布系统 - Agent Skills 后端服务",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ API 路由 ============

class SelfVideoRouter:
    def __init__(self, app: FastAPI):
        self.app = app
        self.setup_routes()

    def setup_routes(self):
        print(f"自媒体创作接口初始化")
        
        @self.app.get("/api/self_video/skills")
        async def get_skills():
            """获取所有Skills列表"""
            skills = skill_registry.get_all()
            return {
                "skills": [s.to_dict() for s in skills],
                "workflow_order": skill_registry.get_workflow_order()
            }
        
        
        @self.app.get("/api/self_video/skills/{skill_id}")
        async def get_skill(skill_id: str):
            """获取单个Skill信息"""
            skill = skill_registry.get(skill_id)
            if not skill:
                raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")
            return skill.to_dict()
        
        
        @self.app.post("/api/self_video/workflow/run")
        async def run_workflow(request: WorkflowRequest):
            """
            运行完整工作流（流式响应）
            返回 Server-Sent Events (SSE) 流
            """
            # 创建LLM配置
            llm_config = settings.get_llm_config(type=LLMProvider.DS)
            # if request.config:
            #     llm_config = LLMConfig(
            #         provider=request.config.get("provider", "openai"),
            #         base_url=request.config.get("base_url", settings.LLM_BASE_URL),
            #         api_key=request.config.get("api_key", settings.LLM_API_KEY),
            #         model=request.config.get("model", settings.LLM_MODEL)
            #     )
            # llm_config = LLMConfig(
            #     provider = settings.LLM_PROVIDER,
            #     base_url = settings.LLM_BASE_URL,
            #     api_key = settings.LLM_API_KEY,
            #     model = settings.LLM_MODEL
            # )
        
            # 检查API Key
            if not llm_config or not llm_config.api_key:
                if not settings.LLM_API_KEY:
                    raise HTTPException(status_code=400, detail="API Key not configured")
        
            # 创建工作流引擎
            engine = create_workflow_engine(llm_config)
        
            async def event_stream():
                """生成SSE事件流"""
                try:
                    async for event in engine.run_stream(request.topic):
                        event_data = {
                            "event": event.event_type,
                            "skill_id": event.skill_id,
                            "data": event.data,
                            "timestamp": event.timestamp.isoformat()
                        }
                        print(f"event_data:{event_data}")
                        yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
        
                        # 小延迟确保前端能接收
                        await asyncio.sleep(0.01)
        
                    yield "data: [DONE]\n\n"
        
                except Exception as e:
                    error_event = {
                        "event": "error",
                        "data": {"error": str(e)}
                    }
                    yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
        
            return StreamingResponse(
                event_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        
        @self.app.post("/api/self_video/skill/execute")
        async def execute_skill(request: SkillExecuteRequest):
            """
            执行单个Skill（流式响应）
            """
            skill = skill_registry.get(request.skill_id)
            if not skill:
                raise HTTPException(status_code=404, detail=f"Skill not found: {request.skill_id}")
        
            # 创建LLM配置
            llm_config = None
            if request.config:
                llm_config = LLMConfig(
                    provider=request.config.get("provider", "openai"),
                    base_url=request.config.get("base_url", settings.LLM_BASE_URL),
                    api_key=request.config.get("api_key", settings.LLM_API_KEY),
                    model=request.config.get("model", settings.LLM_MODEL)
                )
        
            engine = create_workflow_engine(llm_config)
            engine.context = request.context  # 设置上下文
        
            async def event_stream():
                try:
                    async for event in engine.execute_skill_stream(request.skill_id, request.topic):
                        event_data = {
                            "event": event.event_type,
                            "skill_id": event.skill_id,
                            "data": event.data
                        }
                        yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'event': 'error', 'data': {'error': str(e)}})}\n\n"
        
            return StreamingResponse(
                event_stream(),
                media_type="text/event-stream"
            )
        
        
        @self.app.post("/api/self_video/config/validate")
        async def validate_config(request: ConfigUpdateRequest):
            """验证API配置是否有效"""
            try:
                config = LLMConfig(
                    provider=request.provider,
                    base_url=request.base_url,
                    api_key=request.api_key,
                    model=request.model
                )
                client = get_llm_client(config)
        
                # 发送测试请求
                response = await client.chat_completion(
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=10
                )
        
                return {"valid": True, "message": "配置有效", "test_response": response[:50]}
        
            except Exception as e:
                return {"valid": False, "message": str(e)}
        
        
        @self.app.get("/api/self_video/health")
        async def health_check():
            """健康检查"""
            return {
                "status": "healthy",
                "llm_configured": bool(settings.DS_LLM_API_KEY),
                "skills_count": len(skill_registry.get_all())
            }


# ============ 启动入口 ============

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )