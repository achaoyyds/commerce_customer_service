from dataclasses import dataclass
from enum import Enum
from typing import Any

from task.command.commands import Command


@dataclass(slots=True)
class TaskTurnPlan:

    commands: list[Command]

    @classmethod
    def from_dict(cls, data: dict[str,Any]) -> "TaskTurnPlan":
        return cls(
            commands=[Command.from_dict(cmd) for cmd in data["commands"]]
        )


@dataclass(slots=True)
class KnowledgeTurnPlan:
    intents: list[str]

    @classmethod
    def from_dict(cls, data: dict[str,Any]) -> "KnowledgeTurnPlan":
        return cls(
            intents = data["intents"],
        )

@dataclass(slots=True)
class ChitChatTurnPlan:
    chat: str

    @classmethod
    def from_dict(cls, data: dict[str,Any]) -> "ChitChatTurnPlan":
        return cls(
            chat = data["chat"],
        )

@dataclass(slots=True)
class TurnPlan:
    """
    数据模型
    作用：一轮的路由结果
    """
    task: TaskTurnPlan | None = None
    knowledge: KnowledgeTurnPlan | None = None
    chitchat: ChitChatTurnPlan | None = None
    
    @classmethod
    def from_dict(cls, turn_plan_data: dict[str,Any]) -> "TurnPlan":
        return cls(
            task=TaskTurnPlan.from_dict(turn_plan_data['task']) if turn_plan_data.get('task') is not None else None,
            knowledge=KnowledgeTurnPlan.from_dict(turn_plan_data['knowledge']) if turn_plan_data.get(
                'knowledge') is not None else None,
            chitchat=ChitChatTurnPlan.from_dict(turn_plan_data['chitchat']) if turn_plan_data.get(
                'chitchat') is not None else None
        )

    def activated_tracks(self):
        tracks = []
        if self.task is not None:
            tracks.append("task")
        if self.knowledge is not None:
            tracks.append("knowledge")
        if self.chitchat is not None:
            tracks.append("chitchat")
        return tracks

class ClarifyReason(Enum):
    MISSING_TRACK = "missing_track"
    MULTIPLE_TRACKS = "multiple_tracks"
    MISSING_TASK_COMMANDS = "missing_task_commands"
    MISSING_KNOWLEDGE_INTENT = "missing_knowledge_intent"
    MISSING_FOCUSED_OBJECT = "missing_focused_object"
    OBJECT_REQUIRES_INTENT = "object_requires_intent"
    INVALID_TASK_COMMANDS = "invalid_task_commands"
    MULTIPLE_TASK_FLOWS = "multiple_task_flows"
    UNKNOWN_TASK_FLOW = "unknown_task_flow"


@dataclass(slots=True)
class TurnPlanValidatedResult:
    valid: bool  # true:校验器校验通过  false 校验器没有校验通过
    reason: ClarifyReason | None = None  # 校验器校验后给的原因码
