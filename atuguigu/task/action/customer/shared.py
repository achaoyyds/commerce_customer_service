"""金融业务数据访问层：封装对 finance-data 中台服务的读写调用。

供 task/action/customer 下的 Action 复用，统一走 http_client 的
finance_get / finance_post 完成带鉴权（X-Channel-Code + Bearer customer_no）的调用。
"""
from typing import Any
from urllib.parse import quote
from uuid import uuid4

from atuguigu.infrastructure import http_client as client


def _extract_data(payload: dict | None) -> dict | None:
    """从金融 API 统一响应中提取 data 字段（code != 0 视为失败）。"""
    if not isinstance(payload, dict) or payload.get("code") != 0:
        return None
    data = payload.get("data")
    return data if isinstance(data, dict) else None


def _extract_list(payload: dict | None) -> list[dict]:
    data = _extract_data(payload)
    if data is None:
        return []
    items = data.get("list")
    return items if isinstance(items, list) else []


def _request_no() -> str:
    """写接口幂等控制所需的请求唯一编号。"""
    return f"CS{uuid4().hex.upper()[:16]}"


# ---------------------------------------------------------------- 客户档案

async def fetch_customer(customer_no: str) -> dict | None:
    """查询客户档案。"""
    try:
        r = await client.finance_get(
            f"/customers/{quote(customer_no)}", customer_no=customer_no
        )
        return _extract_data(r.json())
    except Exception:
        return None


# ---------------------------------------------------------------- 账户

async def fetch_customer_accounts(customer_no: str) -> list[dict]:
    """查询客户名下账户列表。"""
    try:
        r = await client.finance_get(
            f"/customers/{quote(customer_no)}/accounts", customer_no=customer_no
        )
        return _extract_list(r.json())
    except Exception:
        return []


async def fetch_account(account_no: str, customer_no: str) -> dict | None:
    """查询账户详情（状态、余额、冻结金额）。"""
    try:
        r = await client.finance_get(
            f"/accounts/{quote(account_no)}", customer_no=customer_no
        )
        return _extract_data(r.json())
    except Exception:
        return None


async def change_account_status(
    account_no: str,
    customer_no: str,
    target_status: str,
    reason: str,
) -> dict | None:
    """变更账户状态（如挂失/冻结）。"""
    body = {
        "request_no": _request_no(),
        "target_status": target_status,
        "reason": reason,
    }
    try:
        r = await client.finance_post(
            f"/accounts/{quote(account_no)}/status-changes",
            customer_no=customer_no,
            json=body,
        )
        return _extract_data(r.json())
    except Exception:
        return None


# ---------------------------------------------------------------- 交易流水

async def fetch_transactions(
    account_no: str, customer_no: str, **params: Any
) -> dict | None:
    """查询账户交易明细，params 可含 start_time/end_time/transaction_type/page_no/page_size。"""
    try:
        r = await client.finance_get(
            f"/accounts/{quote(account_no)}/transactions",
            customer_no=customer_no,
            params=params or None,
        )
        return _extract_data(r.json())
    except Exception:
        return None


# ---------------------------------------------------------------- 贷款

async def fetch_loan_products(customer_no: str, **params: Any) -> list[dict]:
    """查询贷款产品列表。"""
    try:
        r = await client.finance_get(
            "/loan/products", customer_no=customer_no, params=params or None
        )
        return _extract_list(r.json())
    except Exception:
        return []


async def fetch_loan_product(product_code: str, customer_no: str) -> dict | None:
    """查询贷款产品详情。"""
    try:
        r = await client.finance_get(
            f"/loan/products/{quote(product_code)}", customer_no=customer_no
        )
        return _extract_data(r.json())
    except Exception:
        return None


async def fetch_credit_limits(
    customer_no: str, product_code: str | None = None
) -> list[dict]:
    """查询客户授信额度列表。"""
    params = {"product_code": product_code} if product_code else None
    try:
        r = await client.finance_get(
            f"/customers/{quote(customer_no)}/credit-limits",
            customer_no=customer_no,
            params=params,
        )
        return _extract_list(r.json())
    except Exception:
        return []


async def submit_loan_application(
    customer_no: str,
    limit_no: str,
    apply_amount: Any,
    apply_term_months: int,
    repayment_method: str,
    loan_purpose: str = "consume",
) -> dict | None:
    """提交贷款申请。"""
    body = {
        "request_no": _request_no(),
        "customer_no": customer_no,
        "limit_no": limit_no,
        "apply_amount": str(apply_amount),
        "apply_term_months": int(apply_term_months),
        "repayment_method": repayment_method,
        "loan_purpose": loan_purpose,
        "materials": [],
    }
    try:
        r = await client.finance_post(
            "/loan/applications", customer_no=customer_no, json=body
        )
        return _extract_data(r.json())
    except Exception:
        return None


# ---------------------------------------------------------------- 理财

async def fetch_wealth_products(customer_no: str, **params: Any) -> list[dict]:
    """查询可售理财产品列表。"""
    try:
        r = await client.finance_get(
            "/wealth/products", customer_no=customer_no, params=params or None
        )
        return _extract_list(r.json())
    except Exception:
        return []


async def fetch_wealth_product(product_code: str, customer_no: str) -> dict | None:
    """查询理财产品详情。"""
    try:
        r = await client.finance_get(
            f"/wealth/products/{quote(product_code)}", customer_no=customer_no
        )
        return _extract_data(r.json())
    except Exception:
        return None


# ---------------------------------------------------------------- 工单

async def submit_support_ticket(
    customer_no: str,
    ticket_type: str,
    ticket_title: str,
    ticket_content: str,
    related_type: str = "none",
    related_id: int | None = None,
) -> dict | None:
    """创建客服投诉工单。"""
    body = {
        "request_no": _request_no(),
        "customer_no": customer_no,
        "ticket_type": ticket_type,
        "ticket_title": ticket_title,
        "ticket_content": ticket_content,
        "related_type": related_type,
        "related_id": related_id,
    }
    try:
        r = await client.finance_post(
            "/support/tickets", customer_no=customer_no, json=body
        )
        return _extract_data(r.json())
    except Exception:
        return None