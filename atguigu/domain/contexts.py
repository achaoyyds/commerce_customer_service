from dataclasses import field, dataclass, asdict
from typing import Any



@dataclass
class TaskContext:
    flow_id: str
    step_id: str
    slots:dict = field(default_factory=dict)

    def to_dict(self) -> dict[str,Any]:
        return {"flow_id": self.flow_id, "step_id": self.step_id, "slots": self.slots}

    @classmethod
    def from_dict(cls, data: dict[str,Any]) :
        return cls(
            flow_id = data["flow_id"],step_id = data["step_id"],slots = data["slots"]
        )


@dataclass
class SystemContext:
    flow_id: str
    step_id: str | None = None

    def to_dict(self) -> dict[str,Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str,Any]) -> "SystemContext":
        clz = FLOW_ID_TO_CONTEXT_CLASS[data["flow_id"]]
        return clz(**data)

@dataclass
class StartSystemContext(SystemContext):
    started_flow_id:str = ""
    started_flow_name:str = ""



@dataclass
class InterruptSystemContext(SystemContext):
    interrupted_flow_id:str = ""
    interrupted_flow_name:str = ""
    started_flow_id:str = ""
    started_flow_name:str = ""


@dataclass
class CanceledSystemContext(SystemContext):
    canceled_flow_id:str = ""
    canceled_flow_name:str = ""


@dataclass
class ResumeSystemContext(SystemContext):
    resumed_flow_id:str = ""
    resumed_flow_name:str = ""


@dataclass
class CollectSystemContext(SystemContext):
    slot_name:str = ""
    response:dict[str,Any] = field(default_factory=dict)


FLOW_ID_TO_CONTEXT_CLASS = {
    "system_task_started": StartSystemContext,
    "system_task_interrupted": InterruptSystemContext,
    "system_task_canceled": CanceledSystemContext,
    "system_task_resumed": ResumeSystemContext,
    "system_collect_information":CollectSystemContext
}


