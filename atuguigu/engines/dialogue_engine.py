import time

from atuguigu.domain.messages import ProcessedResult, BotMessage, MessageType
from atuguigu.domain.state import DialogueState
from atuguigu.planner.turn_planner import TurnPlanner
from atuguigu.planner.turn_plan_validator import TurnPlanValidator
from atuguigu.handlers.knowledge_handler import KnowledgeHandler
from atuguigu.handlers.task_handler import TaskHandler
from atuguigu.handlers.clarify_responder import ClarifyResponder
from atuguigu.handlers.chitchat_handler import ChitChatHandler
from domain.messages import UserMessage
from task.flows.flows import FlowList


class DialogueEngine:
    def __init__(self,
                 turn_planner:TurnPlanner,
                 turn_plan_validator:TurnPlanValidator,
                 clarify_responder:ClarifyResponder,
                 task_handler:TaskHandler,
                 knowledge_handler:KnowledgeHandler,
                 chitchat_handler:ChitChatHandler,
                 ):
        self._turn_planner = turn_planner
        self._turn_plan_validator = turn_plan_validator
        self._clarify_responder = clarify_responder
        self._task_handler = task_handler
        self._knowledge_handler = knowledge_handler
        self._chitchat_handler = chitchat_handler

    async def handle_message(self,user_message:UserMessage,state: DialogueState) -> ProcessedResult:
        """
        调用LLM 做路由分析、校验分析后的结果、进入对应轨道内部处理、推进流程..
        """
        # 1.开启会话（超时检查/新建）
        self._prepare_session(state)

        # 2.开启本轮 turn(写入pending_turn)
        self._begin_turn(state,user_message)

        # 3.按消息类型分流 枚举判断用is 不能用 ==
        if user_message.type is MessageType.TEXT:
            bot_messages:list[BotMessage] = await self._process_text_message(state,flow_list = self._task_handler.flows_list)

        else:
            state.set_focused_object(user_message.object)
            bot_messages:list[BotMessage] = await self._process_object_message(state)


        # 4.把本轮回复写入 turn ,并提交
        state.pending_turn.bot_messages = bot_messages
        state.commit_pending_turn()


        # 5.返回结果
        return ProcessedResult(
            message_id=user_message.message_id,
            messages=bot_messages
        )

    def _prepare_session(self, state:DialogueState):
        session = state.current_session()
        if session is None:
            state.start_session()
            return
        now = time.time()
        if now - session.activated_at > 60*60:
            state.close_current_session()
            state.reset_runtime_state_for_new_session()
            state.start_session()
        else:
            session.activated_at = now

    def _begin_turn(self, state:DialogueState, user_message:UserMessage):
        state.begin_turn(user_message)

    async def _process_text_message(self, state:DialogueState, flow_list:FlowList) -> list[BotMessage]:
         # 1.利用轮次规划期进行路由判断
         turn_plan = await self._turn_planner.predict(state, flow_list)

         # 2、利用轮次校验器校验轮次的结果

         # 3、如果校验不通过，需要意图澄清器，澄清

         # 4、如果校验通过，找到对应的三条轨道的处理器处理

         # 5、将三条轨道处理的结果 返回
         return [BotMessage(text="你好，欢迎来到电商小二")]

    async def _process_object_message(self, state:DialogueState) -> list[BotMessage]:
        pass




