from pathlib import Path
from atuguigu.planner.turn_planner import TurnPlanner
from atuguigu.planner.turn_plan_validator import TurnPlanValidator
from atuguigu.handlers.chitchat_responder import ChitChatResponder
from atuguigu.handlers.knowledge_handler import KnowledgeHandler
from atuguigu.handlers.task_handler import TaskHandler
from atuguigu.handlers.clarify_responder import ClarifyResponder
from atuguigu.handlers.chitchat_handler import ChitChatHandler
from atuguigu.engines.dialogue_engine import DialogueEngine
from atuguigu.task.action.buider import build_action_runner
from atuguigu.task.command.processor import CommandProcessor
from atuguigu.task.flows.executor import FlowExecutor
from atuguigu.task.flows.loader import FlowLoader
from atuguigu.planner.intents import KNOWLEDGE_INTENTS
from atuguigu.handlers.knowledge_responder import KnowledgeResponder
from atuguigu.handlers.providers.knowledge import ApiOrderProvider, ApiProductProvider, FAQDefaultProvider, RAGDefaultProvider
from atuguigu.handlers.providers.register import ProviderRegister

PROJECT_ROOT_DIR = Path(__file__).resolve().parents[2]
FLOW_CONFIG_DIR = PROJECT_ROOT_DIR / "flow_config"
FLOW_CONFIGS = ["system_flows.yml", "user_flows.yml"]

def build_dialogue_engine():
    flows_list = FlowLoader().load_multi_yarm([FLOW_CONFIG_DIR / flow_config for flow_config in FLOW_CONFIGS])

    return DialogueEngine(
        turn_planner=TurnPlanner(),
        turn_plan_validator=TurnPlanValidator(),
        clarify_responder = ClarifyResponder(),
        task_handler=TaskHandler(
            flows_list = flows_list,
            command_processor=CommandProcessor(),
            flow_executor=FlowExecutor(),
            action_runner=build_action_runner()
    ),
        knowledge_handler= KnowledgeHandler(intents=KNOWLEDGE_INTENTS,
                                           knowledge_responder=KnowledgeResponder(),
                                           providers_register= ProviderRegister(providers=[
                                               ApiOrderProvider(),
                                               ApiProductProvider(),
                                               FAQDefaultProvider(),
                                               RAGDefaultProvider()
                                           ])
                                            ),
        chitchat_handler=ChitChatHandler(chat_responder=ChitChatResponder()),
    )
