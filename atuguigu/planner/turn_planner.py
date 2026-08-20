import json
from dataclasses import asdict
from typing import Any
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from atuguigu.domain.state import DialogueState
from atuguigu.prompt.loader import load_prompt_template
from atuguigu.infrastructure.llm_client import llm
from atuguigu.utils.message_utils import ChatHistoryBuilder
from atuguigu.task.flows.flows import FlowList
from atuguigu.planner.turn_plan import TurnPlan
from planner.intents import KnowledgeIntent


class TurnPlanner:
    async def predict(self, state:DialogueState, flow_list: FlowList,knowledge_intents:dict[str, KnowledgeIntent]) -> TurnPlan:
        """
        职责：调用LLM 做路由分析，判断当前任务该用哪条轨道处理

        """
        prompts_inputs : dict[str,Any] = self._build_prompt_inputs(state,flow_list,knowledge_intents)

        llm_result = await self._invoke_llm(prompts_inputs)
        return llm_result

    def _build_prompt_inputs(self, state:DialogueState, flow_list: FlowList,knowledge_intents:dict[str, KnowledgeIntent]) -> dict[str,Any]:
        # 1.会话相关
        user_message_str = ChatHistoryBuilder._build_message(state.pending_turn.user_message)
        current_conversation_str = ChatHistoryBuilder.build_turns_message(state.current_session().turns[-10:])

        # 2. 任务相关
        active_task_json_str = json.dumps(state.active_task.to_dict(),ensure_ascii=False) if state.active_task else "null"
        interrupted_tasks_json_str = json.dumps([task.to_dict() for task in state.paused_tasks],ensure_ascii=False)

        # 3. 卡片相关
        focused_object_json_str = json.dumps(state.focused_object,ensure_ascii=False) if state.focused_object else "null"

        # 4.清单相关
        available_flow_json_str = json.dumps(
            {
                "flows":[
                    { k:v for k,v in asdict(flow_obj).items() if k != "steps"} for flow_obj in flow_list.flows if not flow_obj.id.startswith("system_")
                ]
            },ensure_ascii=False)

        knowledge_intents_json_str = json.dumps([
            {"id":intent.id,"description":intent.description}
            for intent in knowledge_intents.values()
        ],ensure_ascii=False)

        return {
            "user_message":user_message_str,
            "current_conversation":current_conversation_str,
            "active_task_json":active_task_json_str,
            "interrupted_tasks_json":interrupted_tasks_json_str,
            "focused_object_json":focused_object_json_str,
            "available_flows_json":available_flow_json_str,
            "knowledge_intents_json":knowledge_intents_json_str
        }

    async def _invoke_llm(self, prompts_inputs) ->TurnPlan:
        prompt_template_str = load_prompt_template("turn_plan")

        prompt_template = PromptTemplate.from_template(template=prompt_template_str, template_format="jinja2")

        # 构建langchain 链 JsonOutputParser().invoke(json_str)：把 json 字符串解析成python 字典
        chain = prompt_template | llm | JsonOutputParser()

        llm_result_dict = await chain.ainvoke(prompts_inputs)

        return TurnPlan.from_dict(llm_result_dict)



