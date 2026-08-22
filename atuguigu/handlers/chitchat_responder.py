from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from atuguigu.utils.message_utils import  ChatHistoryBuilder
from atuguigu.infrastructure.llm_client import llm as llm_client
from atuguigu.domain.messages import BotMessage
from atuguigu.domain.state import DialogueState
from atuguigu.prompt.loader import load_prompt_template

class ChitChatResponder:

    async def respond_chat(self,chat:str,state:DialogueState) -> list[BotMessage]:

        # 1.加载闲聊的提示词内容
        prompt_template_str = load_prompt_template("chitchat_respond")

        # 2. 实例化提示词模板对象
        prompt_template = PromptTemplate.from_template(template=prompt_template_str,template_format="jinja2")

        # 3.构建链
        chain = prompt_template | llm_client | StrOutputParser()

        # 4.调用llm
        result = await chain.ainvoke({
            "user_message":chat,
            "history":ChatHistoryBuilder.build_turns_message(state.current_session().turns[-10:]),
        })
        return [BotMessage(text=result)]

