from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, List
import yaml
from atguigu.task.flow.flows import FlowsList, FlowSlot, Flow
from atguigu.task.flow.steps import FlowStep,CollectFlowStep

YAML_PATH = Path(__file__).resolve().parents[3] / "flow_config" / "user_flows.yaml"


class FlowLoader:

    def load_many(self,paths:List[Path]) -> FlowsList:
        flows: List[Flow] = []
        slots: Dict[str,FlowSlot] = {}
        for path in paths:
            single_flows_list = self.load(path)
            flows.extend(single_flows_list.flows)

            duplicate_slot_name = set(slots).intersection(single_flows_list.slots)
            if duplicate_slot_name:
                duplicate_slots = ",".join(duplicate_slot_name)
                f"Duplicate slot definitions found across flow files: {duplicate_slots}."
            slots.update(single_flows_list.slots)
        return FlowsList(slots = slots, flows = flows)

    def load(self,path:Path) -> FlowsList:
        with open(path,'r',encoding="utf-8") as f:
            data:Dict[str,Any] = yaml.safe_load(f)

        slots: Dict[str, FlowSlot] = self._load_slots(data.get("slots",{}))
        flows = self._load_flows(data.get("flows",{}),slots)
        return FlowsList(slots = slots, flows = flows)


    def _load_slots(self, yaml_slots_data:Dict[str,Any]):

        slots = {}
        for slot_name,slot_dict in yaml_slots_data.items():
            slots[slot_name] = FlowSlot(name = slot_name,**slot_dict)

        return slots

    def _load_flows(self, yaml_flows_data: Dict[str, Any], slots_definition: Dict[str, FlowSlot]) -> List[Flow]:
        flows = []
        for flow_id,flow_dict in yaml_flows_data.items():
            steps = [FlowStep.from_dict(step) for step in flow_dict.get("steps",[])]
            flows.append(
                Flow(
                    id = flow_id,
                    description= flow_dict.get("description",""),
                    steps = steps,
                    name = flow_dict.get("name",""),
                    slots = self._collect_flow_slots(slots_definition,steps)
                )
            )
        return flows

    def _collect_flow_slots(self, slots_definition:Dict[str,FlowSlot], steps:List[FlowStep]) -> List[FlowSlot]:

        seen = set()
        flow_slots = []
        for step in steps:
            if not isinstance(step,CollectFlowStep):
                continue

            slot_name = step.slot_name
            if slot_name  in seen:
                continue

            seen.add(slot_name)
            flow_slot = slots_definition.get(slot_name)
            if flow_slot is not None:
                flow_slots.append(flow_slot)
        return flow_slots

if __name__ == "__main__":
    base_path = Path(__file__).parents[3]
    user_flow_path = base_path / 'flow_config' / 'user_flows.yml'
    system_flow_path = base_path / 'flow_config' / 'system_flows.yml'
    loader = FlowLoader()
    flows_list = loader.load_many([user_flow_path, system_flow_path])
    print(flows_list)




