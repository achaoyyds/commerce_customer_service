"""LLM token 消耗埋点：通过 LangChain callback 捕获每次生成的 token 用量。

设计：使用 contextvar 保存「当前轮次」的 token 累计值，callback 在 on_llm_end
时把本次用量的增量累加到 contextvar 里。一轮对话内的多次 LLM 调用（如规划器 +
回复器）都在同一个 async Task 内 await 执行，contextvar 能在其间正确共享，从而
把一个轮次的所有 LLM 调用 token 汇总到一起。
"""
import contextvars
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

_token_usage_ctx: contextvars.ContextVar[dict[str, int]] = contextvars.ContextVar(
    "turn_token_usage", default=None
)


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _extract_usage(llm_output: dict[str, Any] | None) -> dict[str, int] | None:
    if not llm_output:
        return None
    usage = llm_output.get("token_usage") or llm_output.get("usage")
    if not isinstance(usage, dict):
        return None

    prompt = usage.get("prompt_tokens", usage.get("input_tokens", 0))
    completion = usage.get("completion_tokens", usage.get("output_tokens", 0))
    total = usage.get("total_tokens", 0)
    return {
        "prompt_tokens": _as_int(prompt),
        "completion_tokens": _as_int(completion),
        "total_tokens": _as_int(total if total else _as_int(prompt) + _as_int(completion)),
    }


class TokenUsageCallbackHandler(BaseCallbackHandler):
    """把每次 LLM 生成的 token 用量累加到当前轮次 contextvar 中。"""

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        usage = _extract_usage(response.llm_output)
        if usage is None:
            return
        current = _token_usage_ctx.get()
        if current is None:
            current = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        current["prompt_tokens"] += usage["prompt_tokens"]
        current["completion_tokens"] += usage["completion_tokens"]
        current["total_tokens"] += usage["total_tokens"]
        _token_usage_ctx.set(current)


# 单例即可：callback 本身无状态，靠 contextvar 区分不同请求/轮次。
token_usage_handler = TokenUsageCallbackHandler()


def begin_token_usage() -> None:
    """在一轮处理开始前调用，重置本轮的 token 累计值。"""
    _token_usage_ctx.set({"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})


def get_token_usage() -> dict[str, int]:
    """返回本轮已累计的 token 用量。"""
    return _token_usage_ctx.get() or {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def clear_token_usage() -> None:
    _token_usage_ctx.set(None)