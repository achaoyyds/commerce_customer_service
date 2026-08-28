"""金融业务流程 Action 实现。

对应 user_flows.yml 中的 5 个业务动作：
- action_lookup_account_balance   账户余额查询
- action_lookup_transactions      交易流水查询
- action_submit_loan_application  贷款申请提交
- action_report_credit_card_loss  信用卡挂失
- action_submit_complaint_ticket  投诉工单提交

统一复用 shared.py 的数据访问函数，通过 http_client 带鉴权调用 finance-data。
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from atuguigu.domain.messages import BotMessage
from atuguigu.domain.state import DialogueState
from atuguigu.task.action.base import Action, ActionResult
from atuguigu.task.action.customer import shared


# ------------------------------------------------------------------ 通用工具


def _slots(state: DialogueState) -> dict[str, Any]:
    return state.active_task.slots if state.active_task is not None else {}


def _parse_number(value: Any, *, as_int: bool = False) -> Decimal | int | None:
    """从 LLM 填写的槽位文本中提取数值，如 "10000元" -> 10000、"12个月" -> 12。"""
    text = str(value or "").strip()
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        num = Decimal(match.group())
    except InvalidOperation:
        return None
    return int(num) if as_int else num


def _resolve_date_range(raw: Any) -> tuple[str | None, str | None]:
    """把交易日期槽位解析成 (start_time, end_time)，无法解析时返回 (None, None)。"""
    if not raw:
        return None, None
    text = str(raw).strip()
    today = datetime.now().date()
    aliases = {
        "今天": today,
        "昨天": today - timedelta(days=1),
        "前天": today - timedelta(days=2),
    }
    if text in aliases:
        day = aliases[text]
        return f"{day} 00:00:00", f"{day} 23:59:59"
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y年%m月%d日"):
        try:
            day = datetime.strptime(text, fmt).date()
            return f"{day} 00:00:00", f"{day} 23:59:59"
        except ValueError:
            continue
    return None, None


_TRANSACTION_TYPE_CN = {
    "transfer": "转账",
    "consume": "消费",
    "deposit": "存入",
    "withdraw": "取现",
    "refund": "退款",
    "adjustment": "调账",
}


def _format_transactions(data: dict[str, Any] | None) -> str:
    if not isinstance(data, dict) or not data.get("list"):
        return "该时段暂无交易流水。"
    items = data["list"]
    total = data.get("total_count", len(items))
    lines: list[str] = []
    for item in items[:10]:
        t_type = _TRANSACTION_TYPE_CN.get(item.get("transaction_type", ""), item.get("transaction_type", ""))
        amount = item.get("transaction_amount", "")
        at = item.get("transaction_at", "")
        counterparty = item.get("counterparty_name") or item.get("merchant_name") or ""
        suffix = f"（{counterparty}）" if counterparty else ""
        lines.append(f"{at} {t_type} {amount}元{suffix}".strip())
    header = f"共 {total} 笔流水"
    if total > len(items):
        header += f"（仅展示最近 {len(items)} 笔）"
    header += "："
    return header + "\n" + "\n".join(lines)


# ------------------------------------------------------------------ 账户余额查询


class ActionLookupAccountBalance(Action):
    name = "action_lookup_account_balance"

    async def run(self, action_kwargs: dict[str, Any], state: DialogueState) -> ActionResult:
        customer_no = state.sender_id
        account_no = _slots(state).get("account_no")
        if not account_no:
            return ActionResult(messages=[BotMessage(text="未能获取到账户号，请重新输入。")])

        account = await shared.fetch_account(account_no, customer_no)
        if account is None:
            return ActionResult(
                messages=[BotMessage(text="未查询到该账户信息，请核对账户号或银行卡号后重试。")]
            )

        balance = Decimal(str(account.get("balance_amount") or "0"))
        frozen = Decimal(str(account.get("frozen_amount") or "0"))
        available = balance - frozen

        return ActionResult(
            slots={
                "account_status": account.get("account_status", ""),
                "balance_amount": f"{balance:.2f}",
                "frozen_amount": f"{frozen:.2f}",
                "available_amount": f"{available:.2f}",
            }
        )


# ------------------------------------------------------------------ 交易流水查询


class ActionLookupTransactions(Action):
    name = "action_lookup_transactions"

    async def run(self, action_kwargs: dict[str, Any], state: DialogueState) -> ActionResult:
        customer_no = state.sender_id
        slots = _slots(state)
        account_no = slots.get("account_no")
        if not account_no:
            return ActionResult(messages=[BotMessage(text="未能获取到账户号，请重新输入。")])

        start_time, end_time = _resolve_date_range(slots.get("transaction_date"))
        params: dict[str, Any] = {"page_size": 20}
        if start_time and end_time:
            params["start_time"] = start_time
            params["end_time"] = end_time

        data = await shared.fetch_transactions(account_no, customer_no, **params)
        summary = _format_transactions(data)

        return ActionResult(slots={"transaction_summary": summary})


# ------------------------------------------------------------------ 贷款申请


class ActionSubmitLoanApplication(Action):
    name = "action_submit_loan_application"

    async def run(self, action_kwargs: dict[str, Any], state: DialogueState) -> ActionResult:
        customer_no = state.sender_id
        slots = _slots(state)

        amount = _parse_number(slots.get("loan_amount"))
        term = _parse_number(slots.get("loan_term_months"), as_int=True)
        if amount is None or amount <= 0 or term is None or term <= 0:
            return ActionResult(messages=[BotMessage(text="贷款金额或期限信息不完整，请重新填写。")])

        limits = await shared.fetch_credit_limits(customer_no)
        selected: dict[str, Any] | None = None
        for limit in limits:
            try:
                available = Decimal(str(limit.get("available_limit_amount") or "0"))
            except InvalidOperation:
                continue
            if available >= amount:
                selected = limit
                break

        if selected is None:
            return ActionResult(
                messages=[
                    BotMessage(text="当前没有可用的授信额度，请先申请授信或调整贷款金额。")
                ]
            )

        result = await shared.submit_loan_application(
            customer_no=customer_no,
            limit_no=selected["limit_no"],
            apply_amount=amount,
            apply_term_months=term,
            repayment_method="equal_principal_interest",
            loan_purpose=slots.get("loan_purpose") or "consume",
        )

        if result is None:
            return ActionResult(messages=[BotMessage(text="贷款申请提交失败，请稍后重试。")])

        return ActionResult(
            slots={
                "loan_application_no": result.get("application_no", ""),
                "loan_application_status": result.get("application_status", ""),
            }
        )


# ------------------------------------------------------------------ 信用卡挂失


class ActionReportCreditCardLoss(Action):
    name = "action_report_credit_card_loss"

    async def run(self, action_kwargs: dict[str, Any], state: DialogueState) -> ActionResult:
        customer_no = state.sender_id
        slots = _slots(state)
        account_no = slots.get("account_no")
        if not account_no:
            return ActionResult(messages=[BotMessage(text="未能获取到需要挂失的账户号，请重新输入。")])

        reason = str(slots.get("loss_reason") or "信用卡挂失")
        result = await shared.change_account_status(
            account_no=account_no,
            customer_no=customer_no,
            target_status="frozen",
            reason=reason,
        )

        if result is None:
            return ActionResult(messages=[BotMessage(text="挂失办理失败，请稍后重试或联系人工客服。")])

        current_status = result.get("current_status", "frozen")
        return ActionResult(
            slots={
                "loss_result": f"挂失办理成功，账户「{account_no}」已置为挂失状态（{current_status}）。"
            }
        )


# ------------------------------------------------------------------ 投诉工单


class ActionSubmitComplaintTicket(Action):
    name = "action_submit_complaint_ticket"

    async def run(self, action_kwargs: dict[str, Any], state: DialogueState) -> ActionResult:
        customer_no = state.sender_id
        slots = _slots(state)

        ticket_type = str(slots.get("ticket_type") or "投诉")
        related_tx = str(slots.get("related_transaction_no") or "").strip()
        description = str(slots.get("ticket_description") or "").strip()

        has_related = related_tx and related_tx not in {"无", "没有", "无关联", "none", "None"}
        title = f"{ticket_type}：{related_tx}" if has_related else ticket_type

        parts: list[str] = []
        if has_related:
            parts.append(f"关联交易流水号：{related_tx}")
        if description:
            parts.append(description)
        content = "；".join(parts) if parts else ticket_type

        result = await shared.submit_support_ticket(
            customer_no=customer_no,
            ticket_type=ticket_type,
            ticket_title=title,
            ticket_content=content,
            related_type="none",
            related_id=None,
        )

        if result is None:
            return ActionResult(messages=[BotMessage(text="工单创建失败，请稍后重试。")])

        return ActionResult(slots={"ticket_no": result.get("ticket_no", "")})