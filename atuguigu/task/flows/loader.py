from typing import Any
import yaml
from pathlib import Path
from atuguigu.task.flows.flows import FlowList,FlowSlot,Flow
from atuguigu.task.flows.steps import FlowStep,CollectFlowStep


def _load_slots(slots:dict[str,dict[str,Any]]) -> dict[str,FlowSlot]:
    loaded_slots:dict[str,FlowSlot] = {}
    for slot_name,slot_dict in slots.items():
        loaded_slots[slot_name] = FlowSlot(
            slot_name = slot_name,
            **slot_dict
        )
    return loaded_slots


def _build_flow_slots(step:list[FlowStep], total_slots:dict[str, FlowSlot]) -> dict[str, FlowSlot]:
    flow_slots:dict[str,FlowSlot] = {}
    for step in step:
        if not isinstance(step,CollectFlowStep):
            continue
        slot_name = step.slot_name
        slot = total_slots.get(slot_name)
        if slot is not None:
            flow_slots[slot_name] = slot
    return flow_slots


def _load_flows(flows:dict[str,dict[str,Any]], total_slots:dict[str,FlowSlot]) -> list[Flow] :

    loaded_flows:list[Flow] = []
    for flow_id,flow_dict in flows.items():
        steps = [FlowStep.from_dict(step) for step in flow_dict['steps']]
        loaded_flows.append(Flow(
            id = flow_id,
            name = flow_dict['name'],
            description= flow_dict['description'],
            steps= steps,
            slots = _build_flow_slots(steps,total_slots)
        ))
    return loaded_flows


class FlowLoader:
    """
    流程加载器
    利用 pyyaml 包，将yaml文件解析成对象并且解析后的字典实例化对应的数据模型 最后返回 FlowList
    """

    def _load_signle_yaml(self,path:Path) -> FlowList:
        with open(path,'r',encoding="utf-8") as f:
            flow_dict:dict[str,Any] = yaml.safe_load(f.read())

        flows:dict[str,dict[str,Any]] = flow_dict.get("flows")
        slots:dict[str,dict[str,Any]]= flow_dict.get("slots",{})

        loaded_slots:dict[str,FlowSlot] = _load_slots(slots)
        loaded_flows: list[Flow] = _load_flows(flows,loaded_slots)
        return FlowList(flows = loaded_flows,slots = loaded_slots)

    def load_multi_yarm(self,paths:list[Path]) -> FlowList:
        flows:list[Flow] = []
        slots:dict[str,FlowSlot] = {}
        for path in paths:
            flowList = self._load_signle_yaml(path)
            flows.extend(flowList.flows)
            slots.update(flowList.slots)
        return FlowList(flows = flows,slots = slots)


if __name__ == '__main__':
    flow_loader = FlowLoader()
    user_flows_path = Path("user_flows.yml")
    sys_flows_path = Path("system_flows.yml")
    final_flow_list = flow_loader.load_multi_yarm([user_flows_path,sys_flows_path])
    print(final_flow_list)












