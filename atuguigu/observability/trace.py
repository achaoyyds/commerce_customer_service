"""轮次 trace 上下文收集器：记录本轮的处理轨道、耗时、token 等元数据。"""
from dataclasses import dataclass


@dataclass(slots=True)
class TurnTrace:
    """一次对话轮次（turn）的执行链路快照，对应 dialogue_turn 表。"""

    sender_id: str
    session_id: str
    turn_id: str
    message_id: str
    track: str | None = None  # task/knowledge/chitchat/clarify/object
    flow_id: str | None = None  # 命中流程 code（task/object 轨道）
    clarify_reason: str | None = None  # 澄清原因（clarify 轨道）
    user_text: str | None = None
    bot_text: str | None = None
    latency_ms: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0