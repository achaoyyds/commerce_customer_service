from atuguigu.task.flows.flows import FlowList
from domain.messages import BotMessage
from task.command.commands import Command


class TaskHandler:
    def __init__(self,flows_list: FlowList):
        self.flows_list = flows_list

    async def handle(self, state, commands:list[Command]) -> list[BotMessage]:
        """
        根据commands 中的命令 真正的处理流程(开启业务流程、恢复业务流程、取消业务流程、给业务流程设置槽位信息)
        Args:
            state:
            commands:

        Returns:

        """
        pass


