"""
金融业务 API 的 HTTP 客户端封装。

调用 finance-data 中台服务查询账户、交易、贷款、理财等金融数据。

鉴权方式（finance-data dependencies.py）：
- 请求头 X-Channel-Code：渠道编码（dim_channel.channel_code）
- 请求头 Authorization：Bearer <客户号 customer_no>

约定：客服系统将 DialogueState.sender_id 作为 customer_no（即 Bearer token）。
"""

from typing import Any

from httpx import AsyncClient

from atuguigu.config.settings import settings

http_client: AsyncClient | None = None  # 全局变量

# finance-data 所有业务接口的统一前缀
FINANCE_API_PREFIX = "/api/v1"


def init_http_client() -> AsyncClient:
    global http_client
    http_client = AsyncClient(timeout=10.0)
    return http_client


async def close_http_client() -> None:
    if http_client is not None:
        await http_client.aclose()


def _auth_headers(customer_no: str | None) -> dict[str, str]:
    """构造金融 API 鉴权请求头。"""
    headers: dict[str, str] = {"X-Channel-Code": settings.finance_channel_code}
    if customer_no:
        headers["Authorization"] = f"Bearer {customer_no}"
    return headers


def _finance_url(path: str) -> str:
    """finance_api_base_url 为 host:port 形式，此处拼出完整 URL。"""
    return f"http://{settings.finance_api_base_url.rstrip('/')}{FINANCE_API_PREFIX}{path}"


async def finance_get(path: str, customer_no: str | None = None, **kwargs: Any):
    """发起带金融鉴权的 GET 请求，返回 httpx.Response。"""
    headers = _auth_headers(customer_no)
    headers.update(kwargs.pop("headers", {}) or {})
    return await http_client.get(_finance_url(path), headers=headers, **kwargs)


async def finance_post(path: str, customer_no: str | None = None, **kwargs: Any):
    """发起带金融鉴权的 POST 请求，返回 httpx.Response。"""
    headers = _auth_headers(customer_no)
    headers.update(kwargs.pop("headers", {}) or {})
    return await http_client.post(_finance_url(path), headers=headers, **kwargs)