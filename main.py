"""
FastAPI多路由模块化管理系统
展示如何管理几十个API端点的项目结构
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
import logging
from flight_booking.backend.router_api import FlightBookingRouter
from self_media.backend.self_media_api import SelfMediaRouter
from self_video.backend.self_video_api import SelfVideoRouter

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 主应用实例
app = FastAPI(
    title="模块化API管理系统",
    description="演示如何管理大量API端点",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 初始化所有路由器
flight_booking_router = FlightBookingRouter(app)
self_video_router = SelfVideoRouter(app)
self_media_router = SelfMediaRouter(app)

# 根路径
@app.get("/", tags=["根路径"])
async def root():
    return {
        "message": "欢迎使用模块化API管理系统",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "available_endpoints": [
            "/api"
        ]
    }

# 启动命令
if __name__ == "__main__":
    print("启动FastAPI服务器...")
    print("访问 http://127.0.0.1:8001/docs 查看API文档")
    uvicorn.run(app, host="127.0.0.1", port=8001)
