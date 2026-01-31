import dashscope
from app.tools import get_company_info, get_risk_factors
from app.rag import search_db
from app.prompts import RISK_ANALYSIS_PROMPT
from app.config import DASHSCOPE_API_KEY

dashscope.api_key = DASHSCOPE_API_KEY


def run_agent(question: str) -> str:
    # 1️⃣ 先用 RAG 查资料
    rag_text = search_db(question)

    # 2️⃣ 统一构造 Prompt（不再只限制“风险”）
    prompt = f"""
你是专业金融分析师。

以下是与用户问题相关的资料：
{rag_text}

用户问题是：
{question}

请你基于资料和常识，给出清晰、通俗、有结构的回答。
"""

    # 3️⃣ 调用 Qwen
    response = dashscope.Generation.call(
        model="qwen-plus",
        messages=[{"role": "user", "content": prompt}],
        result_format="message"
    )

    return response["output"]["choices"][0]["message"]["content"]
