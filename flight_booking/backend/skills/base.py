"""
机票预订系统 - Skill 基类
/flight_booking/skills/base.py
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel


class SkillInput(BaseModel):
    """Skill输入"""
    user_request: str  # 用户原始请求
    context: Dict[str, Any] = {}  # 上下文信息


class SkillOutput(BaseModel):
    """Skill输出"""
    skill_id: str
    content: str
    data: Dict[str, Any] = {}  # 结构化数据
    success: bool = True
    error: str = ""


class BaseSkill(ABC):
    """Skill 抽象基类"""

    def __init__(self):
        self.id: str = ""
        self.name: str = ""
        self.description: str = ""
        self.icon: str = ""

    @abstractmethod
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        pass

    @abstractmethod
    def get_user_prompt(self, input_data: SkillInput) -> str:
        """获取用户提示词"""
        pass

    def build_messages(self, input_data: SkillInput) -> List[Dict[str, str]]:
        """构建消息列表"""
        return [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": self.get_user_prompt(input_data)}
        ]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon
        }
