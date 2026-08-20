from atuguigu.planner.turn_plan import TurnPlan, ClarifyReason, TurnPlanValidatedResult, KnowledgeTurnPlan
from domain.state import DialogueState
from planner.intents import KnowledgeIntent
from planner.turn_plan import TaskTurnPlan
from task.command.commands import StartFlowCommand, ResumeFlowCommand, CancelFlowCommand, SetSlotsCommand
from task.flows.flows import FlowList


class TurnPlanValidator:
    def validate(self,
                 turn_plan:TurnPlan,
                 state:DialogueState,
                 flow_list:FlowList,
                 knowledge_intents:dict[str, KnowledgeIntent]) -> "TurnPlanValidatedResult":

        # 1. 轨道层面的校验（外部）
        selected_tracks = turn_plan.activated_tracks()

        # 1.1 是否没有命令任何轨道
        if not selected_tracks:
            return self._reject(ClarifyReason.MISSING_TRACK)

        # 1.2 是否命中多条轨道
        if len(selected_tracks) > 1:
            return self._reject(ClarifyReason.MULTIPLE_TRACKS)

        # 2. 轨道内部校验 闲聊不需要校验
        selected_track = selected_tracks[0]
        if selected_track == "task":
            return self._validate_task_track(turn_plan.task,flow_list)
        elif selected_track == "knowledge":
            return self._validate_knowledge_track(turn_plan.knowledge,state,knowledge_intents)
        else:
            return TurnPlanValidatedResult(valid=True)


    def _reject(self, reason:ClarifyReason) :
        return TurnPlanValidatedResult(valid=False,reason = reason)


    def _validate_task_track(self, task:TaskTurnPlan, flow_list:FlowList):
        """
        task轨道4层校验
        1.校验commands 是否为空列表
        2.校验命令类型是否是系统现在支持的四种命令类型
        3.校验命令是否有多个开启业务流程的命令
        4.校验这一个业务流程是否存在【flow_id ----> Flows 查询】
        Args:
            task:
            flow_list:

        Returns:

        """
        # 1. 校验commands是否是空列表
        if not task.commands:
            return self._reject(reason=ClarifyReason.MISSING_TASK_COMMANDS)

        # 2.  校验commands中的命令类型是否是系统现在支持的四种命令类型
        allowed_commands = (StartFlowCommand,ResumeFlowCommand,CancelFlowCommand,SetSlotsCommand)
        if not all([isinstance(cmd,allowed_commands) for cmd in task.commands]):
            return self._reject(reason=ClarifyReason.INVALID_TASK_COMMANDS)

        # 3. 校验command 中是否有多个开启业务流程的命令
        start_flow_cmd = [cmd for cmd in task.commands if isinstance(cmd,StartFlowCommand)]
        if len(start_flow_cmd) > 1:
            return self._reject(reason=ClarifyReason.MULTIPLE_TASK_FLOWS)

        # 4. 校验这一个业务流程是否存在
        # 4.1 如果没有StartFlowCommand，要不要拒绝（不能拒绝）因为可能就不需要开启业务流程，
        # 可能是恢复业务流程、取消业务流程、给业务流程设置槽位，操作已经存在的业务流程
        # 4.2 如果有一个StartFlowCommand，确保这个也是流程真实存在
        if start_flow_cmd:
            start_flow = start_flow_cmd[0]
            flow_id = start_flow.flow
            flow = flow_list.get_flow_by_id(flow_id)
            if flow is None:
                return self._reject(reason=ClarifyReason.UNKNOWN_TASK_FLOW)

        return TurnPlanValidatedResult(valid=True)


    def _validate_knowledge_track(self, knowledge:KnowledgeTurnPlan, state:DialogueState,knowledge_intents:dict[str, KnowledgeIntent]) ->TurnPlanValidatedResult:
        """
        职责：校验知识轨道内部的两个知识意图（要求传入对象）是否有对象
        如果没有则拒绝
        如果有且二者之间类型匹配，不拒绝
        Args:
            knowledge:
            state:
            knowledge_intents:

        Returns:

        """
        focused_object = state.focused_object
        for intent_id in knowledge.intents:
            knowledge_meta = knowledge_intents[intent_id]
            requires_object = knowledge_meta.requires_object

            if requires_object is not None:
                if focused_object is None or focused_object.type != requires_object:
                    return self._reject(reason=ClarifyReason.MISSING_FOCUSED_OBJECT)

        return TurnPlanValidatedResult(valid=True)


