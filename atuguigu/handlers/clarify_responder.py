import json

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from atuguigu.domain.state import DialogueState
from atuguigu.domain.messages import BotMessage
from atuguigu.infrastructure.llm_client import llm
from atuguigu.observability.token_usage import token_usage_handler
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
            return "你是想了解账户信息、交易流水、贷款产品还是理财产品呢？"

        if reason is ClarifyReason.MISSING_TRACK:
            return "你是想先处理业务问题，还是先咨询信息呢？"

        if reason is ClarifyReason.MISSING_TASK_COMMANDS:
            return "你这次是想办理什么业务呢？比如查账户余额、查交易流水、申请贷款或信用卡挂失。"

        if reason is ClarifyReason.OBJECT_REQUIRES_INTENT:
            focused_object = state.focused_object
            if focused_object is not None and focused_object.type == "account":
                return "我已经收到这个账户了。你想查账户余额、交易流水，还是办理其他业务呢？"
            if focused_object is not None and focused_object.type == "loan":
                return "我已经收到这个贷款产品了。你想了解产品详情，还是办理贷款申请呢？"
            if focused_object is not None and focused_object.type == "wealth":
                return "我已经收到这个理财产品了。你想了解产品详情，还是进一步咨询购买呢？"

        return "我还需要再确认一下你的意思，你可以换个更具体的说法告诉我。"


    async def _invoke(self, prompt_inputs) -> list[BotMessage]:
        prompt_template_str = load_prompt_template("clarify_respond")
        prompt_template = PromptTemplate.from_template(prompt_template_str, template_format="jinja2")

        chain = prompt_template | llm | StrOutputParser()

        result = await chain.ainvoke(prompt_inputs, config={"callbacks": [token_usage_handler]})

        return [BotMessage(text=result)]




