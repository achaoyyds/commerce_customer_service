import json

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from atuguigu.domain.state import DialogueState
from atuguigu.domain.messages import BotMessage
from atuguigu.infrastructure.llm_client import llm
from atuguigu.planner.turn_plan import TurnPlanValidatedResult, ClarifyReason
from atuguigu.prompt.loader import load_prompt_template
from atuguigu.utils.message_utils import ChatHistoryBuilder


class ClarifyResponder:
    async def respond(self,reason:ClarifyReason,state:DialogueState) -> list[BotMessage]:
        """
        根据校验结果对象的原因码，利用LLM来润色澄清回复
        Args:
            validated:
            state:

        Returns:

        """

        # 1.构建澄清话术需要的提示词模版变量值
        prompt_inputs = self._build_responder_prompt_inputs(reason,state)

        bot_messages = await self._invoke(prompt_inputs)

        return bot_messages


    def _build_responder_prompt_inputs(self, reason:ClarifyReason, state:DialogueState):
        reason_str = reason.value
        clarify_message_str = self._build_base_response(reason,state)
        focused_object_str = json.dumps(state.focused_object.to_dict(),ensure_ascii=False) if state.focused_object is not None else "null"
        user_message_str = ChatHistoryBuilder._build_message(state.pending_turn.user_message)
        history_str = ChatHistoryBuilder.build_turns_message(state.current_session().turns[-10:])
        return {
            "user_message": user_message_str,
            "history": history_str,
            "focused_object": focused_object_str,
            "clarify_message": clarify_message_str,
            "reason": reason_str,
        }

    def _build_base_response(self,reason: ClarifyReason, state: DialogueState) -> str:
        if reason is ClarifyReason.MULTIPLE_TRACKS:
            return "你这次同时提到了多个方向。我们先处理一个，你想先办业务还是先咨询信息呢？"

        if reason is ClarifyReason.MISSING_FOCUSED_OBJECT:
            return "请先发送你想咨询的对象，我再继续帮你看。"

        if reason is ClarifyReason.MISSING_KNOWLEDGE_INTENT:
            return "你是想了解商品信息、订单信息，还是售后配送规则呢？"

        if reason is ClarifyReason.MISSING_TRACK:
            return "你是想先处理业务问题，还是先咨询信息呢？"

        if reason is ClarifyReason.MISSING_TASK_COMMANDS:
            return "你这次是想办理什么业务呢？比如查订单、查物流，或者申请退款。"

        if reason is ClarifyReason.OBJECT_REQUIRES_INTENT:
            focused_object = state.focused_object
            if focused_object is not None and focused_object.type == "order":
                return "我已经收到这个订单了。你想查订单状态、查物流，还是申请退款呢？"
            if focused_object is not None and focused_object.type == "product":
                return "我已经收到这个商品了。你想了解它的商品信息、发货情况，还是售后相关问题呢？"

        return "我还需要再确认一下你的意思，你可以换个更具体的说法告诉我。"


    async def _invoke(self, prompt_inputs) -> list[BotMessage]:
        prompt_template_str = load_prompt_template("clarify_respond")
        prompt_template = PromptTemplate.from_template(prompt_template_str, template_format="jinja2")

        chain = prompt_template | llm | StrOutputParser()

        result = await chain.ainvoke(prompt_inputs)

        return [BotMessage(text=result)]




