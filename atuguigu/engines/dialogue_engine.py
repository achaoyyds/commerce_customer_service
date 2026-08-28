import time

from atuguigu.domain.messages import ProcessedResult, BotMessage, MessageType, FocusedObject
from atuguigu.domain.state import DialogueState
from atuguigu.planner.turn_planner import TurnPlanner
from atuguigu.planner.turn_plan_validator import TurnPlanValidator
from atuguigu.handlers.knowledge_handler import KnowledgeHandler
from atuguigu.handlers.task_handler import TaskHandler
from atuguigu.handlers.clarify_responder import ClarifyResponder
from atuguigu.handlers.chitchat_handler import ChitChatHandler
from atuguigu.domain.messages import UserMessage
from atuguigu.planner.intents import KnowledgeIntent
from atuguigu.planner.turn_plan import ClarifyReason
from atuguigu.task.command.commands import SetSlotsCommand, StartFlowCommand
from atuguigu.task.flows.flows import FlowList
from atuguigu.task.flows.steps import CollectFlowStep
from atuguigu.observability.trace import TurnTrace
from atuguigu.observability.token_usage import begin_token_usage, get_token_usage


def _message_text(user_message: UserMessage) -> str | None:
    if user_message.text:
        return user_message.text
    if user_message.object is not None:
        return user_message.object.title
    return None


def _messages_text(bot_messages: list[BotMessage]) -> str | None:
    parts = [message.text for message in bot_messages if message.text]
    return "\n".join(parts) if parts else None


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

        # 本轮 trace 相关临时状态（每轮 process_message 开头重置）
        self._last_trace: TurnTrace | None = None
        self._track: str | None = None
        self._flow_id: str | None = None
        self._clarify_reason: str | None = None

    async def process_message(self,user_message:UserMessage,state: DialogueState):
        """
        调用LLM 做路由分析、校验分析后的结果、进入对应轨道内部处理、推进流程..
        """
        start = time.time()
        self._track = None
        self._flow_id = None
        self._clarify_reason = None
        self._last_trace = None
        # 重置本轮 token 累计，供各 LLM 调用点通过 callback 累加
        begin_token_usage()

        # 1.开启会话（超时检查/新建）
        self._prepare_session(state)

        # 2.开启本轮 turn(写入pending_turn)
        self._begin_turn(state,user_message)
        session = state.current_session()
        turn = state.pending_turn

        # 3.按消息类型分流 枚举判断用is 不能用 ==
        if user_message.type is MessageType.TEXT:
            bot_messages:list[BotMessage] = await self._process_text_message(state,
                                                                             flow_list = self._task_handler._flows_list,
                                                                             knowledge_intents = self._knowledge_handler._knowledge_intents)
        else:
            state.set_focused_object(user_message.object)
            bot_messages:list[BotMessage] = await self._process_object_message(user_message.object, state, self._task_handler._flows_list)

        # 4.把本轮回复写入 turn ,并提交
        state.pending_turn.bot_messages = bot_messages
        state.commit_pending_turn()

        # 5.汇总本轮 trace（轨道/流程/耗时/token）
        tokens = get_token_usage()
        self._last_trace = TurnTrace(
            sender_id=user_message.sender_id,
            session_id=session.session_id if session is not None else None,
            turn_id=turn.turn_id if turn is not None else None,
            message_id=user_message.message_id,
            track=self._track,
            flow_id=self._flow_id,
            clarify_reason=self._clarify_reason,
            user_text=_message_text(user_message),
            bot_text=_messages_text(bot_messages),
            latency_ms=int((time.time() - start) * 1000),
            prompt_tokens=tokens["prompt_tokens"],
            completion_tokens=tokens["completion_tokens"],
            total_tokens=tokens["total_tokens"],
        )

        # 6.返回结果
        return ProcessedResult(
            message_id=user_message.message_id,
            messages=bot_messages
        )

    def take_trace(self) -> TurnTrace | None:
        """取出本轮 trace 并清空，供 service 层落库。"""
        trace = self._last_trace
        self._last_trace = None
        return trace

    def _mark_track(self, track: str, flow_id: str | None = None, clarify_reason: str | None = None):
        self._track = track
        self._flow_id = flow_id
        self._clarify_reason = clarify_reason

    def _resolve_task_flow_id(self, commands: list, state: DialogueState) -> str | None:
        for command in commands:
            if isinstance(command, StartFlowCommand):
                return command.flow
        if state.active_task is not None:
            return state.active_task.flow_id
        return None

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

    async def _process_text_message(self, state:DialogueState, flow_list:FlowList,knowledge_intents:dict[str, KnowledgeIntent]) -> list[BotMessage]:
         # 1.利用轮次规划期进行路由判断
         turn_plan = await self._turn_planner.predict(state, flow_list,knowledge_intents)

         # 2、利用轮次校验器校验轮次的结果
         validated = self._turn_plan_validator.validate(turn_plan,state,flow_list,knowledge_intents)

         # 3、如果校验不通过，需要意图澄清器，澄清
         if not validated.valid:
             self._mark_track("clarify", clarify_reason=validated.reason.value if validated.reason else None)
             return await self._clarify_responder.respond(validated.reason,state)

         # 4、如果校验通过，找到对应的三条轨道的处理器处理
         if turn_plan.task is not None:
             self._mark_track("task", flow_id=self._resolve_task_flow_id(turn_plan.task.commands, state))
             return await self._task_handler.handle(state,commands = turn_plan.task.commands)
         elif turn_plan.knowledge is not None:
             self._mark_track("knowledge")
             return await self._knowledge_handler.handle(state,turn_plan.knowledge.intents)
         else:
             self._mark_track("chitchat")
             return await self._chitchat_handler.handle(turn_plan.chitchat.chat,state)



    async def _process_object_message(self,
                                      object_message: FocusedObject,
                                      state: DialogueState,
                                      flows_list: FlowList
                                      ) -> list[BotMessage]:
        # 1.尝试构建SetSlotCommand
        command = self._try_resolve_set_slots_command(object_message,state,flows_list)

        # 2.当前有业务流程且业务流程某一步正好需要点击的卡片
        if command:
            # 继续把流程往前推
            self._mark_track("object", flow_id=self._resolve_task_flow_id([command], state))
            return await self._task_handler.handle(state,commands=[command])

        # 3.当前有业务流程，但是当前业务流程某一步不需要卡片
        # 让流程执行 不会像前推，而是会继续这一步流程
        if state.active_task is not None:
            self._mark_track("object", flow_id=state.active_task.flow_id)
            return await self._task_handler.handle(state,commands=[])

        # 4.当前业务流程没有激活，恢复用户意图是什么
        self._mark_track("clarify", clarify_reason=ClarifyReason.OBJECT_REQUIRES_INTENT.value)
        return await self._clarify_responder.respond(reason= ClarifyReason.OBJECT_REQUIRES_INTENT,state = state)

    def _try_resolve_set_slots_command(self,
                                       object_message: FocusedObject,
                                       state: DialogueState,
                                       flows_list: FlowList
                                       ) -> SetSlotsCommand | None:
        slot_name = {
            "account": "account_no",
            "card": "account_no",
        }.get(object_message.type)

        if slot_name and self._is_build_set_slots_command(slot_name, state, flows_list):
            return SetSlotsCommand(command="set_slots", slots={slot_name: object_message.id})

        return None

    def _is_build_set_slots_command(self, slot_name:str, state:DialogueState, flows_list:FlowList) -> bool:
        """
        处理点击卡片的三种情况
        1.有业务流程，且正好缺 --> True
        2.有业务流程，不缺 ---> False
        3.没有业务流程 （缺与不缺不重要) --- False
        Args:
            slot_name:
            state:
            flows_list:

        Returns: True: 能构建SetSlotsCommand False：不能构建SetSlotsCommand

        """

        activated_task = state.active_task

        # 1.当前任务不存在，返回False
        if activated_task is None:
            return False

        # 2.当前任务不存在，返回False,防御性兜底
        flow_id = activated_task.flow_id
        flow = flows_list.get_flow_by_id(flow_id)
        if flow is None:
            return False

        # 3.当前流程步不需要收集槽位信息，返回False
        step_id = activated_task.step_id
        step = flow.get_step_by_id(step_id)
        if not isinstance(step,CollectFlowStep):
            return False

        # 区分当前业务流程这一步是否需要点击对象  返回True 刚好需要  返回False  不需要
        return step.slot_name == slot_name






