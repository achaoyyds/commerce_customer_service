"""
步骤（节点）设计
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List
from atguigu.task.flow.links import FlowStepLink, FlowStepStaticLink, FlowStepFallbackLink, FlowStepConditionalLink

class FlowStepType(Enum):
    START = 'start'
    ACTION = 'action'
    COLLECT = "collect"
    END = 'end'

@dataclass(slots=True)
class ResponseDefinition:
    model:str = "static"
    text:str = ""
    prompt:str | None = None

@dataclass(slots=True)
class SlotValidation:
    condition:str | None = None
    failure_response:ResponseDefinition | None = None


@dataclass(slots=True)
class FlowStep:
    id:str
    type:FlowStepType
    next: List[FlowStepLink] = field(default_factory=list)
    description: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FlowStep':
        step_type = data['type']
        clz = TYPE_TO_FLOW_STEP[step_type]
        return clz.from_dict(data)

    @staticmethod
    def base_load_fields(base_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        加载各个步骤的基础字段
        """
        return {
            "id":base_data['id'],
            "type":FlowStepType(base_data['type']),
            "description":base_data.get('description',''),
            "next":_build_links(base_data['next']),
        }

def _build_links(link_data:str | list[Dict[str, Any]]) -> List[FlowStepLink]:
        if isinstance(link_data,str):
            return [FlowStepStaticLink(target=link_data)]

        else:
            links = []
            for link_dict in link_data:
                if "if" in link_dict:
                    links.append(FlowStepConditionalLink(condition=link_dict['if'],target=link_dict['then']))
                else:
                    links.append(FlowStepFallbackLink(target=link_dict['else']))
        return links

@dataclass(slots=True)
class StartedFlowStep(FlowStep):

    @classmethod
    def from_dict(cls,step_data: Dict[str, Any]) -> "StartFlowStep":
        return cls(**FlowStep.base_load_fields(step_data))


@dataclass(slots=True)
class ActionFlowStep(FlowStep):

    action:str = ""
    args:Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls,step_data: Dict[str, Any]) -> "ActionFlowStep":
        return cls(**FlowStep.base_load_fields(step_data),
                   action = step_data["action"],
                   args = step_data.get("args",{})
                   )

@dataclass(slots=True)
class EndFlowStep(FlowStep):

    @classmethod
    def from_dict(cls,step_data: Dict[str, Any]) -> "EndFlowStep":
        return cls(**FlowStep.base_load_fields(step_data))

@dataclass(slots=True)
class CollectFlowStep(FlowStep):
    slot_name:str = ""
    response:ResponseDefinition = field(default_factory=ResponseDefinition) # 必填字段（填写的槽位）
    validate:SlotValidation | None = None

    @classmethod
    def from_dict(cls,step_data: Dict[str, Any]) -> "CollectFlowStep":
        return cls(
            **FlowStep.base_load_fields(step_data),
            slot_name = step_data["slot_name"],
            response = ResponseDefinition(**step_data['response']),
            validate = SlotValidation(
                condition= step_data["validation"]["condition"],
                failure_response= ResponseDefinition(
                    **step_data['validation']['failure_response']
                ) if step_data['validate'].get('failure_response') else None
            ) if step_data.get('validate') else None

        )
@dataclass(slots=True)
class EndFlowStep(FlowStep):

    @classmethod
    def from_dict(cls,step_data: dict[str, Any]) -> "EndFlowStep":
        return cls(**FlowStep.base_load_fields(step_data))

TYPE_TO_FLOW_STEP:Dict[str,type[FlowStep]] = {
    "start":StartedFlowStep,
    "action":ActionFlowStep,
    "end":EndFlowStep,
    "collect":CollectFlowStep,
}