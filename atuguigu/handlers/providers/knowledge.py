import json
from typing import Any

from atuguigu.domain.state import DialogueState
from atuguigu.handlers.providers.base import Provider, KnowledgeChunk
from atuguigu.infrastructure import http_client


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


def _object_id(state: DialogueState) -> str | None:
    return state.focused_object.id if state.focused_object else None


class ApiAccountProvider(Provider):
    """账户信息检索：余额、可用余额、冻结金额、账户状态。"""

    provider_id = "api.account"

    async def retrival(self, state: DialogueState) -> list[KnowledgeChunk]:
        account_no = _object_id(state)
        if not account_no:
            return [KnowledgeChunk(content="未提供账户号，无法查询账户信息。")]
        account = await self._fetch_account(account_no, state.sender_id)
        if account is None:
            return [KnowledgeChunk(content=f"未查询到账户 {account_no} 的信息。")]
        return [
            KnowledgeChunk(
                content="账户信息：\n"
                + json.dumps(account, ensure_ascii=False, indent=2)
            )
        ]

    async def _fetch_account(self, account_no: str, customer_no: str) -> dict | None:
        try:
            response = await http_client.finance_get(
                f"/accounts/{account_no}", customer_no=customer_no
            )
            return _extract_data(response.json())
        except Exception:
            return None


class ApiTransactionProvider(Provider):
    """账户交易流水检索：交易金额、时间、交易对象等。"""

    provider_id = "api.transaction"

    async def retrival(self, state: DialogueState) -> list[KnowledgeChunk]:
        account_no = _object_id(state)
        if not account_no:
            return [KnowledgeChunk(content="未提供账户号，无法查询交易流水。")]
        payload = await self._fetch_transactions(account_no, state.sender_id)
        if payload is None:
            return [KnowledgeChunk(content=f"未查询到账户 {account_no} 的交易流水。")]
        return [
            KnowledgeChunk(
                content="交易流水：\n"
                + json.dumps(payload, ensure_ascii=False, indent=2)
            )
        ]

    async def _fetch_transactions(self, account_no: str, customer_no: str) -> dict | None:
        try:
            response = await http_client.finance_get(
                f"/accounts/{account_no}/transactions",
                customer_no=customer_no,
                params={"page_no": 1, "page_size": 20},
            )
            return _extract_data(response.json())
        except Exception:
            return None


class ApiLoanProductProvider(Provider):
    """贷款产品检索：利率、期限、还款方式等。"""

    provider_id = "api.loan_product"

    async def retrival(self, state: DialogueState) -> list[KnowledgeChunk]:
        product_code = _object_id(state)
        if product_code:
            detail = await self._fetch_loan_product(product_code, state.sender_id)
            if detail is None:
                return [KnowledgeChunk(content=f"未查询到贷款产品 {product_code} 的信息。")]
            return [
                KnowledgeChunk(
                    content="贷款产品信息：\n"
                    + json.dumps(detail, ensure_ascii=False, indent=2)
                )
            ]

        products = await self._fetch_loan_products(state.sender_id)
        if not products:
            return [KnowledgeChunk(content="暂未查询到可申请的贷款产品。")]
        return [
            KnowledgeChunk(
                content="贷款产品列表：\n"
                + json.dumps(products, ensure_ascii=False, indent=2)
            )
        ]

    async def _fetch_loan_products(self, customer_no: str) -> list[dict]:
        try:
            response = await http_client.finance_get(
                "/loan/products", customer_no=customer_no
            )
            return _extract_list(response.json())
        except Exception:
            return []

    async def _fetch_loan_product(self, product_code: str, customer_no: str) -> dict | None:
        try:
            response = await http_client.finance_get(
                f"/loan/products/{product_code}", customer_no=customer_no
            )
            return _extract_data(response.json())
        except Exception:
            return None


class ApiWealthProductProvider(Provider):
    """理财产品检索：风险等级、收益率、起购金额等。"""

    provider_id = "api.wealth_product"

    async def retrival(self, state: DialogueState) -> list[KnowledgeChunk]:
        product_code = _object_id(state)
        if product_code:
            detail = await self._fetch_wealth_product(product_code, state.sender_id)
            if detail is None:
                return [KnowledgeChunk(content=f"未查询到理财产品 {product_code} 的信息。")]
            return [
                KnowledgeChunk(
                    content="理财产品信息：\n"
                    + json.dumps(detail, ensure_ascii=False, indent=2)
                )
            ]

        products = await self._fetch_wealth_products(state.sender_id)
        if not products:
            return [KnowledgeChunk(content="暂未查询到可购买的理财产品。")]
        return [
            KnowledgeChunk(
                content="理财产品列表：\n"
                + json.dumps(products, ensure_ascii=False, indent=2)
            )
        ]

    async def _fetch_wealth_products(self, customer_no: str) -> list[dict]:
        try:
            response = await http_client.finance_get(
                "/wealth/products", customer_no=customer_no
            )
            return _extract_list(response.json())
        except Exception:
            return []

    async def _fetch_wealth_product(self, product_code: str, customer_no: str) -> dict | None:
        try:
            response = await http_client.finance_get(
                f"/wealth/products/{product_code}", customer_no=customer_no
            )
            return _extract_data(response.json())
        except Exception:
            return None


class ApiCustomerProvider(Provider):
    """客户档案检索：客户状态、风险等级、KYC 状态等。"""

    provider_id = "api.customer"

    async def retrival(self, state: DialogueState) -> list[KnowledgeChunk]:
        profile = await self._fetch_customer(state.sender_id)
        if profile is None:
            return [KnowledgeChunk(content="未查询到客户档案信息。")]
        return [
            KnowledgeChunk(
                content="客户档案：\n"
                + json.dumps(profile, ensure_ascii=False, indent=2)
            )
        ]

    async def _fetch_customer(self, customer_no: str) -> dict | None:
        try:
            response = await http_client.finance_get(
                f"/customers/{customer_no}", customer_no=customer_no
            )
            return _extract_data(response.json())
        except Exception:
            return None


class FAQDefaultProvider(Provider):
    provider_id = "faq.default"

    async def retrival(self, state: DialogueState) -> list[KnowledgeChunk]:
        """
        TODO 后面对接公司提供好的FAQ检索结果（开发好的、自己开发系统）
        """
        return [KnowledgeChunk(content="暂未对接FAQ,无法查询到有效的知识内容")]


class RAGDefaultProvider(Provider):
    provider_id = "rag.default"

    async def retrival(self, state: DialogueState) -> list[KnowledgeChunk]:
        """
        TODO 后面对接公司提供好的RAG检索结果(开发好的、自己开发系统)
        """
        return [KnowledgeChunk(content="暂未对接RAG,无法查询到有效的知识内容")]