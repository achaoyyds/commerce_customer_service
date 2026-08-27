from dataclasses import asdict

from atuguigu.domain.messages import BotMessage
from atuguigu.domain.state import DialogueState
from atuguigu.task.flows.flows import FlowList
from atuguigu.domain.contexts import SystemCollectInformationContext
from atuguigu.task.action.runner import ActionRunner, ActionCall
from atuguigu.task.flows.links import FlowStepStaticLink, FlowStepConditionLink
from atuguigu.task.flows.steps import FlowStep, StartFlowStep, EndFlowStep, ActionFlowStep, CollectFlowStep


class FlowExecutor:
    async def executor_flow(self,
                            flows_list:FlowList,
                            action_runner: ActionRunner,
                            state:DialogueState) -> list[BotMessage]:
        """
        职责：根据 command_processor 修改后的state 推进流程(业务流程、系统流程)
        Args:
            flows_list:
            action_runner:
            state:

        Returns:

        """
        final_messages = []
        while True:

            # 1.找到action步骤类型
            action_call:ActionCall = self._advance_flow_util_action(flows_list,state)

            # 2.判断action_call有值 判断action_name 是action_xxx才调用
            # 如果action_name是action_response不用管，如果action_name是action_listen则退出，回复信息
            if action_call.action_name == "action_listen":
                break
            else:
                action_result = await action_runner.run(action_call, state)
                final_messages.extend(action_result.messages)
                state.set_slots(action_result.slots)
        return final_messages

    def _advance_flow_util_action(self,
                                  flows_list:FlowList,
                                  state:DialogueState):
        """
        职责：对内真正推进流程
        Args:
            flows_list:
            state:

        Returns:

        """
        while True:
            # 1.获取当前的上下文对象 系统流程上下文或者业务流程上下文【先获取到的是系统流程上下文】
            current_task = state.current_task()
            if current_task is None:
                return ActionCall(action_name="action_listen")

            # 2. 获取要推进的流程ID（业务流程ID 系统流程ID）
            flow_id  = current_task.flow_id

            # 3. 获取流程对象（业务流程对象 系统流程对象）
            flow = flows_list.get_flow_by_id(flow_id)

            # 4. 获取步骤ID
            step_id = current_task.step_id

            # 5.获取步骤对象
            step = flow.get_step_by_id(step_id)

            # 6.执行步骤
            action_call = self._run_step(step,state)

            if action_call is not None:
                return action_call

    def _run_step(self,  step: FlowStep, state:DialogueState)-> ActionCall | None:
        if isinstance(step, StartFlowStep):
            return self._run_start_step(step, state)
        elif isinstance(step, EndFlowStep):
            return self._run_end_step(state)
        elif isinstance(step, ActionFlowStep):
            return self._run_action_step(step, state)
        elif isinstance(step, CollectFlowStep):
            return self._run_collect_step(step, state)
        else:
            return None

    def _run_start_step(self, step:StartFlowStep, state:DialogueState):
        # 1.推进下一步
        self._advance_flow_step(step,state)

        return None

    def _run_end_step(self, state:DialogueState):

        # 先结束系统流程 下一次才能切换到业务流程
        if state.active_system_task is not None:
            state.end_system_task()

        elif state.active_task is not None:
            state.end_active_task()
        else:
            pass

        return None

    def _run_action_step(self, step, state:DialogueState):

        # 1.推进下一步
        self._advance_flow_step(step,state)

        # 2. 构建Action
        action_kwargs = step.args
        if isinstance(action_kwargs,str):
            # 将业务定义的槽位描述 带出去
            action_kwargs = asdict(state.active_system_task)['response']

        # 3. 返回Action
        return ActionCall(action_name=step.action,action_kwargs=action_kwargs)


    def _run_collect_step(self, step:CollectFlowStep, state:DialogueState):
        """
        收集槽位信息 （业务流程会进来）
        特点：
        1. 用户可能会配置槽位的校验
        2. 该方法会执行两次
        2.1 第一次执行的目的是为了触发system_collect_information 系统流程，收集用户槽位信息
        2.2 第二次执行的目的是对用户填写的槽位信息做校验
        a) 如果校验通过，执行后面的步骤
        b) 如果校验不通过，删除填错的槽位，重新触发system_collect_information系统流程，再收集用户的槽位信息
        Args:
            FlowStep:
            state:

        Returns:

        """
        # 1. 尝试利用点击的卡片
        self._try_fill_slots_from_focused_object(step,state)

        # 2. 判断,如果当前业务流程的插槽有收集步骤需要的槽位信息
        if state.active_task.slots.get(step.slot_name):
            # 第二次进来，代表用户填写了槽位，判断填写的槽位是否合法
            if step.validate:
                if self._eval_condition(step.validate.condition,state):
                    # 推进下一步
                    self._advance_flow_step(step,state)
                    return None
                else:
                    # 移除填错的不满足条件的槽位信息
                    state.remove_slots(step.slot_name)
                    # 给响应
                    if step.validate.failure_response is None:
                        # 给默认的响应
                        return ActionCall(action_name="action_response",action_kwargs={
                            "text":"您填写的信息有误，请重新填写!"
                        })
                    else:
                        return ActionCall(action_name="action_response",action_kwargs=asdict(step.validate.failure_response))
            # 没有校验
            else:
                self._advance_flow_step(step,state)

        else:
            state.start_system_task(SystemCollectInformationContext(
                flow_id = "system_collect_information",
                step_id = "start",
                response = asdict(step.response),
                slot_name=step.slot_name
            ))
            return None

    def _advance_flow_step(self, step, state):

        # 1. 根据当前step 找到下一个step_id
        next_step_id = self._select_next_step_id(step,state)

        # 2. 更新当前任务的step_id
        state.current_task().step_id = next_step_id

    def _select_next_step_id(self, step: FlowStep,
                        state: DialogueState):

        for next_link in step.next:

            if isinstance(next_link,FlowStepStaticLink):
                return next_link.target

            if isinstance(next_link,FlowStepConditionLink):
                validated = self._eval_condition(next_link.condition,state)
                if validated:
                    return next_link.target
            if isinstance(next_link,FlowStepStaticLink):
                return next_link.target

    def _eval_condition(self, condition, state):
        #  "slots.get('product_id')"    # eval
        context = {
            'slots':state.active_task.slots,
            'context':asdict(state.active_system_task) if state.active_system_task is not None else {},
        }
        return eval(condition,{},context)

    def _try_fill_slots_from_focused_object(self,
                                            step: CollectFlowStep,
                                            state: DialogueState):
        # 1.判断当前业务流程以及卡片对象是否有
        if state.active_task is None or state.focused_object is None:
            return

        # 2.利用点击的卡片
        excepted_slots_mapping = {
            "account": "account_no",
            "card": "account_no",
        }
        excepted_slots = excepted_slots_mapping.get(state.focused_object.type)
        # 3.当前业务流程的这一步需要的槽位名称是否和期望的一致,并且active_task 对应的槽位为空
        if step.slot_name == excepted_slots and not state.active_task.slots.get(step.slot_name):
            state.set_slots({step.slot_name:state.focused_object.id})

if __name__ == '__main__':
        # condition_str= "slots.get('product_id')=='12345'"
        condition_str = "slots.get('product_id')=='123456' and data.get('name')=='ls'"

        context = {
            "slots": {
                "product_id": "123456"
            },
            "data": {
                "name": "ls"
            }
        }
        print(eval(condition_str, {}, context))









