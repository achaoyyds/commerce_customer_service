import json
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
from atuguigu.handlers.providers.knowledge import (
    ApiAccountProvider,
    ApiTransactionProvider,
    ApiLoanProductProvider,
    ApiWealthProductProvider,
    ApiCustomerProvider,
    FAQDefaultProvider,
    RAGDefaultProvider,
)
from atuguigu.handlers.providers.register import ProviderRegister
from atuguigu.admin.cfg_repository import CfgReleaseRepository
from atuguigu.infrastructure import db_client

PROJECT_ROOT_DIR = Path(__file__).resolve().parents[2]
FLOW_CONFIG_DIR = PROJECT_ROOT_DIR / "flow_config"
FLOW_CONFIGS = ["system_flows.yml", "user_flows.yml"]


async def _load_flows_list():
    """优先从数据库最新已发布快照加载流程，失败时回退到 YAML 文件。"""
    try:
        async with db_client.session_factory() as session:
            release = await CfgReleaseRepository(session).get_latest_published("flow", "ALL")
            if release is not None:
                return FlowLoader().load_from_dict(json.loads(release.snapshot_json))
    except Exception as exc:  # noqa: BLE001 - 加载失败需兜底，不能中断引擎构建
        print(f"[engine_builder] 从数据库加载流程失败，回退 YAML：{exc}")
    return FlowLoader().load_multi_yarm([FLOW_CONFIG_DIR / flow_config for flow_config in FLOW_CONFIGS])


async def build_dialogue_engine():
    flows_list = await _load_flows_list()

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
                                               ApiAccountProvider(),
                                               ApiTransactionProvider(),
                                               ApiLoanProductProvider(),
                                               ApiWealthProductProvider(),
                                               ApiCustomerProvider(),
                                               FAQDefaultProvider(),
                                               RAGDefaultProvider()
                                           ])
                                            ),
        chitchat_handler=ChitChatHandler(chat_responder=ChitChatResponder()),
    )
