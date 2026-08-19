from pathlib import Path
from atuguigu.planner.turn_planner import TurnPlanner
from atuguigu.planner.turn_plan_validator import TurnPlanValidator
from atuguigu.handlers.knowledge_handler import KnowledgeHandler
from atuguigu.handlers.task_handler import TaskHandler
from atuguigu.handlers.clarify_responder import ClarifyResponder
from atuguigu.handlers.chitchat_handler import ChitChatHandler
from engines.dialogue_engine import DialogueEngine
from task.flows.loader import FlowLoader

PROJECT_ROOT_DIR = Path(__file__).resolve().parents[2]
FLOW_CONFIG_DIR = PROJECT_ROOT_DIR / "flow_config"
FLOW_CONFIGS = ["system_flows.yml", "user_flows.yml"]

def build_dialogue_engine():
    flows_list = FlowLoader.load_multi_yarm([ FLOW_CONFIG_DIR / flow_config  for flow_config in FLOW_CONFIGS])

    return DialogueEngine(
        turn_planner=TurnPlanner(),
        turn_plan_validator=TurnPlanValidator(),
        clarify_responder = ClarifyResponder(),
        task_handler=TaskHandler(flows_list = flows_list),
        knowledge_handler= KnowledgeHandler(),
        chitchat_handler=ChitChatHandler()
    )
