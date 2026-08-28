from dataclasses import dataclass

@dataclass(slots=True)
class KnowledgeIntent:
    id: str
    description: str
    provider_ids: list[str]
    requires_object: str | None = None

KNOWLEDGE_INTENTS: dict[str, KnowledgeIntent] = {
    # ---- 实时业务数据查询（走 finance-data API Provider）----
    "account_info": KnowledgeIntent(
        id="account_info", description="银行账户信息咨询（余额、可用余额、冻结金额、账户状态）",
        provider_ids=["api.account"], requires_object="account",
    ),
    "transaction_info": KnowledgeIntent(
        id="transaction_info", description="账户交易流水、转账记录、收支明细查询",
        provider_ids=["api.transaction"], requires_object="account",
    ),
    "loan_product_info": KnowledgeIntent(
        id="loan_product_info", description="贷款产品咨询（利率、期限、额度、还款方式）",
        provider_ids=["api.loan_product"],
    ),
    "wealth_product_info": KnowledgeIntent(
        id="wealth_product_info", description="理财产品咨询（风险等级、收益率、起购金额）",
        provider_ids=["api.wealth_product"],
    ),
    "customer_info": KnowledgeIntent(
        id="customer_info", description="客户档案、账户状态、信用情况查询",
        provider_ids=["api.customer"],
    ),
    # ---- FAQ / 知识库检索（兜底）----
    "deposit_info": KnowledgeIntent(
        id="deposit_info", description="存款产品及利率咨询",
        provider_ids=["faq.default", "rag.default"],
    ),
    "credit_card_info": KnowledgeIntent(
        id="credit_card_info", description="信用卡产品、权益、年费咨询",
        provider_ids=["faq.default", "rag.default"],
    ),
    "fund_info": KnowledgeIntent(
        id="fund_info", description="基金产品咨询（类型、净值、风险等级）",
        provider_ids=["faq.default", "rag.default"],
    ),
    "finance_policy": KnowledgeIntent(
        id="finance_policy", description="金融政策、手续费规则、还款规则、风险提示咨询",
        provider_ids=["faq.default", "rag.default"],
    ),
    "general_finance_info": KnowledgeIntent(
        id="general_finance_info", description="金融通用信息咨询",
        provider_ids=["faq.default", "rag.default"],
    ),
}