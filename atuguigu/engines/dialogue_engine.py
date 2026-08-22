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
from atuguigu.task.command.commands import SetSlotsCommand
from atuguigu.task.flows.flows import FlowList
from atuguigu.task.flows.steps import CollectFlowStep


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

    async def process_message(self,user_message:UserMessage,state: DialogueState):
        """
        调用LLM 做路由分析、校验分析后的结果、进入对应轨道内部处理、推进流程..
        """
        # 1.开启会话（超时检查/新建）
        self._prepare_session(state)

        # 2.开启本轮 turn(写入pending_turn)
        self._begin_turn(state,user_message)

        # 3.按消息类型分流 枚举判断用is 不能用 ==
        if user_message.type is MessageType.TEXT:
            bot_messages:list[BotMessage] = await self._process_text_message(state,
                                                                             flow_list = self._task_handler._flows_list,
                                                                             knowledge_intents = self._knowledge_handler.intents)
        else:
            state.set_focused_object(user_message.object)
            bot_messages:list[BotMessage] = await self._process_object_message(user_message.object, state, self._task_handler.flows_list)

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

    async def _process_text_message(self, state:DialogueState, flow_list:FlowList,knowledge_intents:dict[str, KnowledgeIntent]) -> list[BotMessage]:
         # 1.利用轮次规划期进行路由判断
         turn_plan = await self._turn_planner.predict(state, flow_list,knowledge_intents)

         # 2、利用轮次校验器校验轮次的结果
         validated = self._turn_plan_validator.validate(turn_plan,state,flow_list,knowledge_intents)

         # 3、如果校验不通过，需要意图澄清器，澄清
         if not validated.valid:
             return await self._clarify_responder.respond(validated.reason,state)

         # 4、如果校验通过，找到对应的三条轨道的处理器处理
         if turn_plan.task is not None:
             return await self._task_handler.handle(state,commands = turn_plan.task.commands)
         elif turn_plan.knowledge is not None:
             return await self._knowledge_handler.handle(turn_plan.knowledge.intents,state)
         else:
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
            return await self._task_handler.handle(state,commands=[command])

        # 3.当前有业务流程，但是当前业务流程某一步不需要卡片
        # 让流程执行 不会像前推，而是会继续这一步流程
        if state.active_task is not None:
            return await self._task_handler.handle(state,commands=[])

        # 4.当前业务流程没有激活，恢复用户意图是什么
        return await self._clarify_responder.respond(reason= ClarifyReason.OBJECT_REQUIRES_INTENT,state = state)

    def _try_resolve_set_slots_command(self,
                                       object_message: FocusedObject,
                                       state: DialogueState,
                                       flows_list: FlowList
                                       ) -> SetSlotsCommand | None:
        if object_message.type == "order":
            if self._is_build_set_slots_command("order_number",state,flows_list):
                return SetSlotsCommand(command="set_slots",slots={"order_number":object_message.id})

        if object_message.type == "product":
            if self._is_build_set_slots_command("product_id",state,flows_list):
                return SetSlotsCommand(command="set_slots",slots={"product_id":object_message.id})

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






