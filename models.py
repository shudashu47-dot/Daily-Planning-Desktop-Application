"""
数据模型层 - 定义任务和日计划的数据结构
"""

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional


@dataclass
class Task:
    """单个任务的数据模型"""
    content: str
    priority: str = "medium"   # high, medium, low
    category: str = "其他"      # 工作, 学习, 生活, 其他
    completed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    tomato_count: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**data)

    def mark_completed(self, completed: bool = True):
        self.completed = completed
        if completed:
            self.completed_at = datetime.now().isoformat()
        else:
            self.completed_at = None

    @property
    def priority_value(self) -> int:
        """优先级数值，用于排序"""
        return {"high": 3, "medium": 2, "low": 1}.get(self.priority, 2)


@dataclass
class DayPlan:
    """单日计划的数据模型"""
    date: str
    tasks: List[Task] = field(default_factory=list)
    daily_note: str = ""

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "tasks": [t.to_dict() for t in self.tasks],
            "daily_note": self.daily_note
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DayPlan":
        tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        return cls(
            date=data.get("date", ""),
            tasks=tasks,
            daily_note=data.get("daily_note", "")
        )

    @property
    def completed_count(self) -> int:
        return sum(1 for t in self.tasks if t.completed)

    @property
    def total_count(self) -> int:
        return len(self.tasks)

    @property
    def completion_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return round(self.completed_count / self.total_count * 100, 1)
