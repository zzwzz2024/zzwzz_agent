"""
机票预订系统 - FastAPI 主入口
/flight_booking/main.py
"""
import json
import asyncio
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from flight_booking.backend.config import settings, LLMConfig
from flight_booking.backend.skills.definitions import skill_registry
from flight_booking.backend.workflow.engine import create_workflow_engine
from flight_booking.backend.llm_client import get_llm_client
from flight_booking.backend.flight_booking_api import flight_tools


# ============ 请求/响应模型 ============

class BookingRequest(BaseModel):
    """预订请求"""
    user_request: str  # 用户原始请求，如"帮我订一张明天10点从海口到北京的机票"
    config: Optional[dict] = None


class ConfigValidateRequest(BaseModel):
    """配置验证请求"""
    provider: str = "openai"
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o-mini"


# ============ 应用初始化 ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🛫 Flight Booking Agent Starting...")
    print(f"📍 Server: http://{settings.HOST}:{settings.PORT}")
    print(f"🤖 LLM: {settings.LLM_PROVIDER}/{settings.LLM_MODEL}")
    print(f"📦 Skills: {[s.id for s in skill_registry.get_all()]}")
    yield
    print("👋 Flight Booking Agent Shutting down...")


app = FastAPI(
    title="智能机票预订 API",
    description="基于 Agent Skills 的智能机票预订系统",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ API 路由 ============

@app.get("/")
async def root():
    return {
        "name": "智能机票预订系统",
        "version": "1.0.0",
        "status": "running",
        "description": "基于Agent Skills的智能机票预订服务"
    }


class FlightBookingRouter:
    def __init__(self, app: FastAPI):
        self.app = app
        self.setup_routes()

    # def setup_routes(self):
    #     @self.app.get("/users", tags=["用户管理"], summary="获取所有用户")
    #     async def get_users(skip: int = 0, limit: int = 100):
    #         logger.info(f"获取用户列表，跳过{skip}条，限制{limit}条")
    #         return []


    def setup_routes(self):
        print(f"机票预定接口初始化")

        @self.app.get("/api/flight_booking/health")
        async def health_check():
            return {
                "status": "healthy",
                "llm_configured": bool(settings.LLM_API_KEY),
                "skills_count": len(skill_registry.get_all())
            }

        @self.app.post("/api/flight_booking/config/validate")
        async def validate_config(request: ConfigValidateRequest):
            """验证API配置"""
            try:
                config = LLMConfig(
                    provider=request.provider,
                    base_url=request.base_url,
                    api_key=request.api_key,
                    model=request.model
                )
                client = get_llm_client(config)

                response = await client.chat_completion(
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=10
                )

                return {"valid": True, "message": "配置有效", "test_response": response[:50]}

            except Exception as e:
                return {"valid": False, "message": str(e)}

        @self.app.get("/api/flight_booking/skills")
        async def get_skills():
            """获取所有Skills"""
            skills = skill_registry.get_all()
            return {
                "skills": [s.to_dict() for s in skills],
                "workflow_order": skill_registry.get_workflow_order()
            }

        @self.app.get("/api/flight_booking/flights/search")
        async def search_flights(
                departure: str = "海口",
                arrival: str = "北京",
                date: str = "",
                time: str = ""
        ):
            """直接查询航班（测试用）"""
            flights = flight_tools.search_flights(
                departure_city=departure,
                arrival_city=arrival,
                date=date,
                preferred_time=time
            )
            return {"flights": flights, "count": len(flights)}

        @self.app.post("/api/flight_booking/booking/run", tags=["用户管理"], summary="获取所有用户")
        async def run_booking(request: BookingRequest):
            """
            运行机票预订工作流（SSE流式）
            """
            # 重置工具状态
            flight_tools.orders = {}
            flight_tools.current_passengers = []

            # 创建LLM配置
            llm_config = None
            if request.config:
                llm_config = LLMConfig(
                    provider=request.config.get("provider", "openai"),
                    base_url=request.config.get("base_url", settings.LLM_BASE_URL),
                    api_key=request.config.get("api_key", settings.LLM_API_KEY),
                    model=request.config.get("model", settings.LLM_MODEL)
                )

            if not llm_config or not llm_config.api_key:
                if not settings.LLM_API_KEY:
                    raise HTTPException(status_code=400, detail="API Key not configured")

            engine = create_workflow_engine(llm_config)

            async def event_stream():
                try:
                    async for event in engine.run_stream(request.user_request):
                        event_data = {
                            "event": event.event_type,
                            "skill_id": event.skill_id,
                            "data": event.data,
                            "timestamp": event.timestamp.isoformat()
                        }
                        yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.01)

                    yield "data: [DONE]\n\n"

                except Exception as e:
                    error_event = {"event": "error", "data": {"error": str(e)}}
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

# ============ 启动入口 ============

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
