"""
上下文对象的类型（抽象）
业务流程上下文

系统流程上下文：继承思想+字典的映射
每次实例化 TaskContext 对象时，自动创建一个全新独立的空字典 {}，避免多个对象共用同一个 dict 导致的数据污染。
可变类型（dict、list、对象）→ default_factory=xxx
"""


from dataclasses import dataclass,field,asdict
from typing import Any

@dataclass(slots=True)
class TaskContext:
    """
    业务流程上下文：
    flow_id:业务流程id，确认业务流式哪一个的唯一标识，比如：order_status_query
    step_id: 业务流程的步骤ID，确认业务流程的步骤，已经走了哪些步，该走哪一步
    slots:业务流程缺少的槽位信息
    """
    flow_id: str
    step_id: str
    slots: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "step_id": self.step_id,
            "slots": self.slots,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskContext":
        return cls(
            flow_id = data['flow_id'],
            step_id = data['step_id'],
            slots = data['slots']
        )

@dataclass(slots=True)
class SystemContext:
    flow_id: str
    step_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SystemContext":
        flow_id = data['flow_id']
        clz = SYSTEM_CONTEXT_TO_CLASS[flow_id]
        return clz(**data)

@dataclass(slots=True)
class SystemTaskStartedContext(SystemContext):
    started_flow_id: str
    started_flow_name: str

@dataclass(slots = True)
class SystemTaskInterruptedContext(SystemContext):
    interrupted_flow_id: str
    interrupted_flow_name: str
    started_flow_id: str
    started_flow_name: str

@dataclass(slots=True)
class SystemTaskResumedContext(SystemContext):
    resumed_flow_id: str
    resumed_flow_name: str

@dataclass(slots=True)
class SystemTaskCanceledContext(SystemContext):
    canceled_flow_id: str
    canceled_flow_name: str

@dataclass(slots=True)
class SystemCollectInformationContext(SystemContext):
    response: dict[str, Any] # 要告诉用户业务流程槽位缺少什么
    slot_name : str # 缺少槽位名字【槽位信息：槽位名字：槽位值】 TODO 主要是为了判断

@dataclass(slots=True)
class ResumeFailedSystemContext(SystemContext):
    """没有找到可恢复的业务流程时使用。"""

SYSTEM_CONTEXT_TO_CLASS: dict[str,type[SystemContext]] = {
    "system_task_started": SystemTaskStartedContext,
    "system_task_interrupted": SystemTaskInterruptedContext,
    "system_task_resumed": SystemTaskResumedContext,
    "system_task_canceled": SystemTaskCanceledContext,
    "system_collect_information": SystemCollectInformationContext,
    "system_task_resume_failed":ResumeFailedSystemContext
}