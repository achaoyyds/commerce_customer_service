from typing import Any

from jinja2 import Template
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from atuguigu.utils.message_utils import ChatHistoryBuilder
from atuguigu.infrastructure.llm_client import llm as llm_client
from atuguigu.observability.token_usage import token_usage_handler
from atuguigu.domain.messages import BotMessage
from atuguigu.domain.state import DialogueState
from atuguigu.task.action.base import Action, ActionResult


class ActionResponse(Action):
    name = "action_response"

    async def run(self, action_kwargs: dict[str, Any],state:DialogueState) -> ActionResult:

        """
        职责：负责将 yarm 中的响应内容，获取返回给用户
        响应内容：有站位。双花括号：交给jinja2 模板引擎渲染
        Args:
            action_kwargs:
            state:

        Returns:

        """
        # 1. 获取响应的模式
        action_response_mode = action_kwargs.get('mode','static')

        # 2. 判断模式
        if action_response_mode == 'rephrase':
            # a) 获取要响应的内容
            response_text = action_kwargs['text']

            # b) 渲染获取的响应内容
            rendered_text = self._render(response_text,state)

            # c) 获取提示词
            prompt = action_kwargs['prompt']

            # d) 调用llm
            rewritten = await self.call_llm(state, prompt, rendered_text)

            return ActionResult(messages=[BotMessage(text=rewritten)])

        elif action_response_mode == "generate":
            # a) 获取提示词
            prompt = action_kwargs['prompt']

            # b) 调用llm
            rewritten = await self.call_llm(state, prompt, "")

            return ActionResult(messages=[BotMessage(text=rewritten)])

        else:
            # "static"
            # a) 获取响应的内容
            response_text = action_kwargs['text']

            # b) 渲染获取的响应内容
            rendered_text = self._render(response_text, state)

            # c) 直接返回
            return ActionResult(messages=[BotMessage(text=rendered_text)])


    def _render(self, response_text, state):

        template = Template(response_text)
        render_str = template.render(slots = state.active_task.slots if state.active_task else {},context = state.active_system_task)
        return render_str

    async def call_llm(self,
                        state:DialogueState,
                        prompt:str,
                        rendered_text):
        # 1. 实例化提示词模版对象
        prompt_template = PromptTemplate.from_template(template=prompt)

        # 2. 构建chain
        chain = prompt_template | llm_client | StrOutputParser()

        # 3. 调用chain
        rewritten = await chain.ainvoke({
            "history": ChatHistoryBuilder.build_turns_message(state.current_session().turns[-5:]),
            "user_message": ChatHistoryBuilder._build_message(state.pending_turn.user_message),
            "current_response": rendered_text
        }, config={"callbacks": [token_usage_handler]})

        # 4. 返回
        return rewritten




