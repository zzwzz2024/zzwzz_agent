"""
机票预订系统 - 工作流引擎
/flight_booking/workflow/engine.py
"""
import asyncio
import json
import re
from typing import Dict, Any, AsyncGenerator, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from flight_booking.backend.skills.base import SkillInput
from flight_booking.backend.skills.definitions import skill_registry
from flight_booking.backend.llm_client import LLMClient, get_llm_client
from flight_booking.backend.config import LLMConfig

class WorkflowStatus(Enum):
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
    """工作流引擎 - 事件驱动，支持流式输出"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or get_llm_client()
        self.context: Dict[str, Any] = {}
        self.status = WorkflowStatus.IDLE
        self.current_skill_index = -1
        self._cancelled = False

    def reset(self):
        self.context = {}
        self.status = WorkflowStatus.IDLE
        self.current_skill_index = -1
        self._cancelled = False

    def cancel(self):
        self._cancelled = True
        self.status = WorkflowStatus.CANCELLED

    def _extract_json_data(self, content: str) -> Dict[str, Any]:
        """从LLM输出中提取JSON数据"""
        try:
            # 查找 ```json ... ``` 块
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
        return {}

    async def execute_skill_stream(
            self,
            skill_id: str,
            user_request: str
    ) -> AsyncGenerator[WorkflowEvent, None]:
        """执行单个Skill（流式）"""
        skill = skill_registry.get(skill_id)
        if not skill:
            yield WorkflowEvent(
                event_type="skill:error",
                skill_id=skill_id,
                data={"error": f"Skill not found: {skill_id}"}
            )
            return

        yield WorkflowEvent(
            event_type="skill:start",
            skill_id=skill_id,
            data={"skill": skill.to_dict()}
        )

        # 构建输入
        input_data = SkillInput(user_request=user_request, context=self.context)
        messages = skill.build_messages(input_data)

        full_content = ""
        try:
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

            # 提取结构化数据
            extracted_data = self._extract_json_data(full_content)
            if extracted_data:
                self.context[f"{skill_id}_data"] = extracted_data

            yield WorkflowEvent(
                event_type="skill:complete",
                skill_id=skill_id,
                data={"content": full_content, "extracted_data": extracted_data}
            )

        except Exception as e:
            yield WorkflowEvent(
                event_type="skill:error",
                skill_id=skill_id,
                data={"error": str(e)}
            )
            raise

    async def run_stream(self, user_request: str) -> AsyncGenerator[WorkflowEvent, None]:
        """运行完整工作流（流式）"""
        if self.status == WorkflowStatus.RUNNING:
            yield WorkflowEvent(
                event_type="workflow:error",
                data={"error": "Workflow is already running"}
            )
            return

        self.reset()
        self.status = WorkflowStatus.RUNNING

        yield WorkflowEvent(
            event_type="workflow:start",
            data={"user_request": user_request}
        )

        skill_order = skill_registry.get_workflow_order()

        try:
            for i, skill_id in enumerate(skill_order):
                if self._cancelled:
                    break

                self.current_skill_index = i

                async for event in self.execute_skill_stream(skill_id, user_request):
                    yield event

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
                    data={"context": {k: v for k, v in self.context.items() if not k.endswith("_data")}}
                )

        except Exception as e:
            self.status = WorkflowStatus.ERROR
            yield WorkflowEvent(
                event_type="workflow:error",
                data={"error": str(e)}
            )

    def get_progress(self) -> Dict[str, Any]:
        total = len(skill_registry.get_workflow_order())
        current = self.current_skill_index + 1
        return {
            "current": current,
            "total": total,
            "percentage": round((current / total) * 100) if total > 0 else 0,
            "status": self.status.value
        }


def create_workflow_engine(config: Optional[LLMConfig] = None) -> WorkflowEngine:
    llm_client = get_llm_client(config)
    return WorkflowEngine(llm_client)
