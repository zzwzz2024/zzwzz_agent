# Agent 多功能智能代理系统

## 📖 项目简介

本项目是一个多功能智能代理系统，包含多个子模块，分别服务于不同的业务场景：
- **Flight Booking**：航班预订系统
- **Self Media**：自媒体文章创作系统
- **Self Video**：短视频创作系统

每个子模块均采用前后端分离架构，后端基于 FastAPI 实现，前端通过 HTML 页面交互。

## 🚀 功能模块

### Flight Booking
- 提供航班查询、预订和管理功能。
- 支持多供应商接入和价格比较。

### Self Media
- 自动生成高质量公众号文章。
- 包含选题分析、素材收集、内容审核等功能。

### Self Video
- 支持短视频脚本创作、封面设计、背景音乐推荐等。
- 提供完整的发布与推广策略。

## 📁 项目结构

. ├── flight_booking/ 
│ ├── backend/ # 后端服务 
│ ├── front/ # 前端页面 
│ └── README.md 
├── self_media/ 
│ ├── backend/ # 后端服务 
│ ├── front/ # 前端页面 
│ └── README.md 
├── self_video/ 
│ ├── backend/ # 后端服务 
│ ├── front/ # 前端页面 
│ └── README.md 
├── main.py # 主入口文件 
├── main.html # 主页面 
├── requirements.txt # Python 依赖 
├── .env.example # 环境变量示例 
└── README.md # 项目说明

## 🛠️ 快速开始

### 1. 安装依赖

```
bash
pip install -r requirements.txt
```

### 2. 配置环境变量
复制 `.env.example` 并重命名为 `.env`，填写必要配置项。

### 3. 启动服务

uvicorn main:app --host 0.0.0.0 --port 8000 --reload

访问地址：http://localhost:8000 查看主页面。

## 🔌 支持的模型提供商
- OpenAI
- 智谱AI
- DeepSeek
- 通义千问
- 自定义兼容 OpenAI API 的服务

## 📜 许可证
MIT License
