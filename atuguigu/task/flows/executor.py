from atuguigu.domain.messages import BotMessage
from atuguigu.domain.state import DialogueState
from atuguigu.task.flows.flows import FlowList

class FlowExecutor:
    async def executor_flow(self,flows_list:FlowList,state:DialogueState):

        return [BotMessage(text="机器人回复")]

