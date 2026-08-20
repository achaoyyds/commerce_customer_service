from dataclasses import dataclass,field

from atuguigu.task.flows.steps import  FlowStep


@dataclass(slots=True)
class FlowSlot:
    slot_name: str # 字典中的key
    type: str
    label: str
    description: str


@dataclass(slots=True)
class Flow:
    id: str
    name: str
    description: str
    steps: list[FlowStep] # 步骤（节点）具体化
    slots: dict[str, FlowSlot] = field(default_factory=dict) #将某一个业务流程中需要收集的槽位信息额外的补充到Flow对象的slots属性中

    def get_step_by_id(self,step_id: str) -> FlowStep | None:
        for step in self.steps:
            if step.id == step_id:
                return step
        return None


@dataclass(slots=True)
class FlowList:
    flows: list[Flow]
    slots: dict[str, FlowSlot] = field(default_factory=dict)

    def get_flow_by_id(self, flow_id: str) -> Flow | None:
        for flow in self.flows:
            if flow.id == flow_id:
                return flow
        return None






