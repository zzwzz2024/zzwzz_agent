"""
工作流引擎
/backend/workflow/engine.py
"""
import asyncio
from typing import Dict, Any, AsyncGenerator, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from self_media.backend.base import SkillInput, SkillOutput
from self_media.backend.definitions import skill_registry
from self_media.backend.llm_client import LLMClient, get_llm_client
from self_media.backend.config import LLMConfig


class WorkflowStatus(Enum):
    """工作流状态"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class WorkflowEvent:
    """工作流事件"""
    event_type: str
    skill_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class WorkflowEngine:
    """
    工作流引擎
    负责按顺序执行Skills，管理上下文，发射事件
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or get_llm_client()
        self.context: Dict[str, str] = {}
        self.status = WorkflowStatus.IDLE
        self.current_skill_index = -1
        self._cancelled = False

    def reset(self):
        """重置工作流"""
        self.context = {}
        self.status = WorkflowStatus.IDLE
        self.current_skill_index = -1
        self._cancelled = False

    def cancel(self):
        """取消工作流"""
        self._cancelled = True
        self.status = WorkflowStatus.CANCELLED

    async def execute_skill_stream(
            self,
            skill_id: str,
            topic: str
    ) -> AsyncGenerator[WorkflowEvent, None]:
        """
        执行单个Skill（流式）
        返回事件流
        """
        skill = skill_registry.get(skill_id)
        if not skill:
            yield WorkflowEvent(
                event_type="skill:error",
                skill_id=skill_id,
                data={"error": f"Skill not found: {skill_id}"}
            )
            return

        # 发送开始事件
        yield WorkflowEvent(
            event_type="skill:start",
            skill_id=skill_id,
            data={"skill": skill.to_dict()}
        )

        # 构建输入
        input_data = SkillInput(topic=topic, context=self.context)
        messages = skill.build_messages(input_data)

        full_content = ""
        try:
            # 流式调用LLM
            async for chunk in self.llm_client.stream_chat_completion(messages):
                if self._cancelled:
                    yield WorkflowEvent(
                        event_type="skill:cancelled",
                        skill_id=skill_id
                    )
                    return

                full_content += chunk
                yield WorkflowEvent(
                    event_type="skill:stream",
                    skill_id=skill_id,
                    data={"chunk": chunk, "content": full_content}
                )

            # 保存到上下文
            self.context[skill_id] = full_content

            # 发送完成事件
            yield WorkflowEvent(
                event_type="skill:complete",
                skill_id=skill_id,
                data={"content": full_content}
            )

        except Exception as e:
            yield WorkflowEvent(
                event_type="skill:error",
                skill_id=skill_id,
                data={"error": str(e)}
            )
            raise

    async def run_stream(self, topic: str) -> AsyncGenerator[WorkflowEvent, None]:
        """
        运行完整工作流（流式）
        返回事件流
        """
        if self.status == WorkflowStatus.RUNNING:
            yield WorkflowEvent(
                event_type="workflow:error",
                data={"error": "Workflow is already running"}
            )
            return

        self.reset()
        self.status = WorkflowStatus.RUNNING

        # 发送工作流开始事件
        yield WorkflowEvent(
            event_type="workflow:start",
            data={"topic": topic}
        )

        skill_order = skill_registry.get_workflow_order()

        try:
            for i, skill_id in enumerate(skill_order):
                if self._cancelled:
                    break

                self.current_skill_index = i

                # 执行Skill并转发所有事件
                async for event in self.execute_skill_stream(skill_id, topic):
                    yield event

                    # 如果是错误事件，停止工作流
                    if event.event_type == "skill:error":
                        self.status = WorkflowStatus.ERROR
                        yield WorkflowEvent(
                            event_type="workflow:error",
                            data={"error": event.data.get("error")}
                        )
                        return

            if not self._cancelled:
                self.status = WorkflowStatus.COMPLETED
                yield WorkflowEvent(
                    event_type="workflow:complete",
                    data={"context": self.context}
                )

        except Exception as e:
            self.status = WorkflowStatus.ERROR
            yield WorkflowEvent(
                event_type="workflow:error",
                data={"error": str(e)}
            )

    def get_progress(self) -> Dict[str, Any]:
        """获取进度信息"""
        total = len(skill_registry.get_workflow_order())
        current = self.current_skill_index + 1
        return {
            "current": current,
            "total": total,
            "percentage": round((current / total) * 100) if total > 0 else 0,
            "status": self.status.value
        }


def create_workflow_engine(config: Optional[LLMConfig] = None) -> WorkflowEngine:
    """创建工作流引擎实例"""
    llm_client = get_llm_client(config)
    return WorkflowEngine(llm_client)