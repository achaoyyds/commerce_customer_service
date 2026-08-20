from atuguigu.task.flows.flows import FlowList
from domain.messages import BotMessage
from task.command.commands import Command
from task.command.processor import CommandProcessor
from task.flows.executor import FlowExecutor


class TaskHandler:
    def __init__(self,
                 flows_list: FlowList,
                 command_processor:CommandProcessor,
                 flow_executor:FlowExecutor):
        self._flows_list = flows_list
        self._command_processor = command_processor
        self._flow_executor = flow_executor

    async def handle(self, state, commands:list[Command]) -> list[BotMessage]:
        """
        根据commands 中的命令 真正的处理流程(开启业务流程、恢复业务流程、取消业务流程、给业务流程设置槽位信息)
        Args:
            state:
            commands:

        Returns:

        """
        # 1. 利用命令[指令]处理器处理对应的命令[指令]
        self._command_processor.process_commands(commands,state,self._flows_list)

        # 2. 利用流程推进器推荐流程
        bot_messages = await self._flow_executor.executor_flow(self._flows_list,state)

        # 3. 返回机器人回复的消息
        return bot_messages



