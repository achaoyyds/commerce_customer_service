from enum import Enum
from dataclasses import dataclass,field
from typing import Any

from atuguigu.task.flows.links import FlowStepLink

@dataclass(slots=True)
class ResponseDefinition:
    text: str
    mode : str = "static" # 【static:自己定义的话 generate: llm 从0生成】
    prompt: str | None = None

@dataclass(slots=True)
class SlotValidate:
    condition: str
    failure_response: ResponseDefinition | None = None


class FlowStepType(Enum):
    START = "start"
    END = "end"
    ACTION = "action"
    COLLECT = "collect"

@dataclass(slots=True)
class FlowStep:
    """
    流程步骤基类
    """
    id: str
    type: FlowStepType
    next: list[FlowStepLink]

    @staticmethod
    def from_dict(step_data: dict[str,Any]) -> 'FlowStep':
        """
        data: dict[str,Any]
        Args:
            step_data:  某一个业务流程的步骤字典对象

        Returns:

        """
        flow_step_type = step_data['type']
        clz = FLOW_STEP_TO_CLASS[flow_step_type]
        # 由于每个子类的字段不同，所以调用子类自己的from_dict方法来处理
        return clz.from_dict(step_data)

    # 统一处理子类的共同字段
    @staticmethod
    def _load_base_fields(step_data: dict[str,Any]) -> dict[str,Any]:
        return {
            "id": step_data['id'],
            "type": FlowStepType(step_data['type']),
            "next": FlowStepLink.from_dict(step_data['next']),
        }

@dataclass(slots=True)
class StartFlowStep(FlowStep):

    @classmethod
    def from_dict(cls,step_data: dict[str,Any]) -> 'StartFlowStep':
        return cls(
            **FlowStep._load_base_fields(step_data)
        )

@dataclass(slots=True)
class EndFlowStep(FlowStep):

    @classmethod
    def from_dict(cls,step_data: dict[str,Any]) -> 'EndFlowStep':
        return cls(
            **FlowStep._load_base_fields(step_data)
        )

@dataclass(slots=True)
class ActionFlowStep(FlowStep):
    action: str
    args: dict[str,Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls,step_data: dict[str,Any]) -> 'ActionFlowStep':
        return cls(
            **FlowStep._load_base_fields(step_data),
            action = step_data['action'],
            args = step_data.get('args',{})
        )


@dataclass(slots=True)
class CollectFlowStep(FlowStep):
    slot_name: str
    response: ResponseDefinition
    validate: SlotValidate | None = None

    @classmethod
    def from_dict(cls,step_data: dict[str,Any]) -> 'CollectFlowStep':
        return cls(
            **FlowStep._load_base_fields(step_data),
            slot_name = step_data['slot_name'],
            response = ResponseDefinition(
                text=step_data['response']['text'],
                mode = step_data['response'].get('mode',"static"),
                prompt= step_data['response'].get('prompt')
            ),
            validate = SlotValidate(
                condition=step_data['validate']['condition'],
                failure_response=ResponseDefinition(
                    text= step_data['validate']['failure_response']['text'],
                    mode = step_data['validate']['failure_response'].get('mode','static'),
                    prompt=step_data['validate']['failure_response'].get('prompt')
                ) if step_data['validate'].get('failure_response') is not None else None
            ) if step_data.get('validate') is not None else None
        )

FLOW_STEP_TO_CLASS : dict[str,type[FlowStep]] = {
    "start": StartFlowStep,
    "end": EndFlowStep,
    "action": ActionFlowStep,
    "collect": CollectFlowStep,
}



