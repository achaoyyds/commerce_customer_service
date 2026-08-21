from atuguigu.domain.contexts import (SystemTaskCanceledContext, SystemTaskResumedContext,
                                      SystemTaskInterruptedContext, SystemTaskStartedContext,
                                       ResumeFailedSystemContext)
from atuguigu.domain.state import DialogueState
from atuguigu.task.command.commands import Command, StartFlowCommand, SetSlotsCommand, ResumeFlowCommand, \
    CancelFlowCommand
from atuguigu.task.flows.flows import FlowList
from atuguigu.domain.contexts import TaskContext

class CommandProcessor:
    def process_commands(self,
                         commands: list[Command],
                         state: DialogueState,
                         flows_list:FlowList):
        """
        根据commands 中的命令，分别处理命令对应的动作，本质是交给流程推进器修改state中和任务相关的属性

        """
        for command in commands:
            self._apply(command,state,flows_list)

    def _apply(self, command:Command, state:DialogueState, flows_list:FlowList):
        """
        根据美国具体的命令类型，执行对应的逻辑处理
        Args:
            command:
            state:
            flows_list:

        Returns:

        """
        if isinstance(command, StartFlowCommand):
            self._handle_start_flow(command, state, flows_list)
        elif isinstance(command, SetSlotsCommand):
            self._handle_update_slots(command, state)
        elif isinstance(command, ResumeFlowCommand):
            self._handle_resume_flow(command,state,flows_list)
        elif isinstance(command, CancelFlowCommand):
            self._handle_cancel_flow(state,flows_list)
        else:
            pass

    def _handle_start_flow(self, command:StartFlowCommand, state:DialogueState, flows_list:FlowList):
        # 获取目标流程对象
        started_flow = flows_list.get_flow_by_id(command.flow)

        # 获取当前业务流程上下文对象
        active_task = state.active_task

        # 情况一：当前有活跃任务
        if active_task is not None:

            # a) 如果开启的任务是当前active_task，则直接结束
            if active_task.flow_id == started_flow.id:
                return

            # b) 删除暂停栈中和目标流程相同的业务流程上下文对象e
            state.remove_paused_tasks(flow_id=started_flow.id)

            # c) 获取中断业务流程的流程ID & 名字
            interrupted_flow_id = active_task.flow_id
            interrupted_flow_name = flows_list.get_flow_by_id(interrupted_flow_id).name

            # d) 中断当前正在执行的业务流程上下文
            state.interrupt_active_task()

            # e) 激活业务流程 上下文
            state.start_task(TaskContext(
                flow_id=started_flow.id,
                step_id="start"
            ))

            # f) 激活“中断系统流程"上下文
            state.start_system_task(
                SystemTaskInterruptedContext(
                    flow_id= "system_task_interrupted",
                    step_id="start",
                    interrupted_flow_id=interrupted_flow_id,
                    interrupted_flow_name=interrupted_flow_name,
                    started_flow_id=started_flow.id,
                    started_flow_name=started_flow.name
                )
            )

        else:
            # a) 删除暂停栈中和目标流程相同的业务流程上下文对象
            state.remove_paused_tasks(flow_id=started_flow.id)

            # b) “激活业务流程”上下文
            state.start_task(TaskContext(
                flow_id=started_flow.id,
                step_id="start"
            ))

            # c) “激活开启系统流程"上下文
            state.start_system_task(SystemTaskStartedContext(
                flow_id="system_task_started",
                step_id="start",
                started_flow_id=started_flow.id,
                started_flow_name=started_flow.name
            ))

    def _handle_update_slots(self, command:SetSlotsCommand, state:DialogueState):
        state.set_slots(command.slots)

    def _handle_resume_flow(self, command:ResumeFlowCommand, state:DialogueState, flows_list:FlowList):
        """
        职责： 恢复业务流程
        Args:
            command:
            state:
            flows_list:

        Returns:

        """
        resumed_flow_id = command.flow

        active_task = state.active_task

        if active_task is not None:
            if resumed_flow_id is None:
                return

            if active_task.flow_id == resumed_flow_id:
                return

            interrupted_flow_id = active_task.flow_id
            interrupted_flow_name = flows_list.get_flow_by_id(interrupted_flow_id).name
            state.interrupt_active_task()
            resumed = state.resume_task(flow_id=resumed_flow_id)
            if not resumed:
                state.resume_task()
                state.start_system_task(ResumeFailedSystemContext(
                    flow_id="system_task_resume_failed",
                    step_id="start",
                ))
                return
            # 3.5 恢复目标业务流程成功
            state.start_system_task(SystemTaskInterruptedContext(
                flow_id="system_task_interrupted",
                step_id="start",
                interrupted_flow_id=interrupted_flow_id,
                interrupted_flow_name=interrupted_flow_name,
                started_flow_id=resumed_flow_id,
                started_flow_name=flows_list.get_flow_by_id(resumed_flow_id).name
            ))
            return
        else:
            # a) 恢复指定的业务流程
            resumed = state.resume_task(flow_id=resumed_flow_id)

            # b) 恢复失败
            if not resumed:
                state.start_system_task(ResumeFailedSystemContext(
                    flow_id="system_task_resume_failed",
                    step_id="start",
                ))
                return
            resumed_flow_id = state.active_task.flow_id
            resumed_flow_name = flows_list.get_flow_by_id(resumed_flow_id).name

            # c) 恢复成功
            state.start_system_task(SystemTaskResumedContext(
                flow_id="system_task_resumed",
                step_id="start",
                resumed_flow_id=resumed_flow_id,
                resumed_flow_name=resumed_flow_name,
            ))

    def _handle_cancel_flow(self, state:DialogueState, flows_list:FlowList):
        active_task = state.active_task
        state.cancel_active_task()
        state.start_system_task(SystemTaskCanceledContext(
            flow_id="system_task_canceled",
            step_id="start",
            canceled_flow_id=active_task.flow_id,
            canceled_flow_name=flows_list.get_flow_by_id(active_task.flow_id).name
        ))


