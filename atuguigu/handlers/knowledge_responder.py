from atuguigu.domain.state import DialogueState
from atuguigu.handlers.providers.base import KnowledgeChunk
from atuguigu.prompt.loader import load_prompt_template
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from atuguigu.infrastructure.llm_client import llm as llm_client
from atuguigu.observability.token_usage import token_usage_handler
from atuguigu.utils.message_utils import ChatHistoryBuilder
from atuguigu.domain.messages import BotMessage


class KnowledgeResponder:

    async def respond(self,
                      chunks:list[KnowledgeChunk],
                      state:DialogueState) -> list[BotMessage]:
        # 1.加载提示词模板内容
        prompt_template_str = load_prompt_template("knowledge_respond")

        # 2.实例化提示词模板对象
        prompt_template = PromptTemplate.from_template(template=prompt_template_str,
                                                       template_format="jinja2")

        # 3.定义chain
        chain = prompt_template | llm_client | StrOutputParser()

        # 4.调用llm
        result = await chain.ainvoke({
            "user_message":ChatHistoryBuilder._build_message(state.pending_turn.user_message),
            "history":ChatHistoryBuilder.build_turns_message(state.current_session().turns[-10:0]),
            "knowledge_content":"\n\n".join([chunk.content for chunk in chunks ])
        }, config={"callbacks": [token_usage_handler]})
        return [BotMessage(text=result)]
