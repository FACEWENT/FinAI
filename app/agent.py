from http import HTTPStatus
import dashscope
from app.tools import get_company_info, get_risk_factors
from app.rag import search_db
from app.prompts import RISK_ANALYSIS_PROMPT
from app.config import DASHSCOPE_API_KEY

dashscope.api_key = DASHSCOPE_API_KEY


def run_agent(question: str) -> str:
    # 1️⃣ 先用 RAG 查资料
    rag_text, has_local = search_db(question)

    # 2️⃣ 统一构造 Prompt（不再只限制“风险”）
    prompt = _build_prompt(question, rag_text, has_local)

    # 3️⃣ 调用 Qwen
    response = dashscope.Generation.call(
        model="qwen-plus",
        messages=[{"role": "user", "content": prompt}],
        result_format="message"
    )

    return response["output"]["choices"][0]["message"]["content"]


def _build_prompt(question: str, rag_text: str, has_local: bool) -> str:
    if has_local:
        local_block = f"""
以下是与用户问题可能相关的本地资料：
{rag_text}
"""
        local_rule = "仅当你确实使用了这些本地资料时，才可以在回答中提及“本地资料/资料依据”等表述。"
    else:
        local_block = "\n本地资料：无。\n"
        local_rule = "本地资料为空时，回答中禁止出现“本地资料/根据资料/资料依据”等表述。"

    prompt = f"""
你是专业金融分析师。

用户问题是：
{question}

{local_block}

请你基于可用信息和常识，给出清晰、通俗、有结构的回答。
{local_rule}
"""
    return prompt


def _extract_content(response) -> str:
    # Support both dict-like and object-like responses from dashscope SDK
    output = None
    if isinstance(response, dict):
        output = response.get("output")
    else:
        output = getattr(response, "output", None)

    if not output:
        return ""

    choices = None
    if isinstance(output, dict):
        choices = output.get("choices") or []
    else:
        choices = getattr(output, "choices", None) or []

    if not choices:
        return ""

    first = choices[0]
    message = None
    if isinstance(first, dict):
        message = first.get("message") or {}
    else:
        message = getattr(first, "message", None) or {}

    if isinstance(message, dict):
        return message.get("content") or ""
    return getattr(message, "content", "") or ""


def run_agent_stream(question: str):
    # 1️⃣ 先用 RAG 查资料
    rag_text, has_local = search_db(question)

    # 2️⃣ 统一构造 Prompt（不再只限制“风险”）
    prompt = _build_prompt(question, rag_text, has_local)

    # 3️⃣ 流式调用 Qwen
    responses = dashscope.Generation.call(
        model="qwen-plus",
        messages=[{"role": "user", "content": prompt}],
        result_format="message",
        stream=True,
        incremental_output=True,
    )

    for response in responses:
        status_code = None
        if isinstance(response, dict):
            status_code = response.get("status_code")
        else:
            status_code = getattr(response, "status_code", None)

        if status_code is not None and status_code != HTTPStatus.OK:
            message = None
            if isinstance(response, dict):
                message = response.get("message")
            else:
                message = getattr(response, "message", None)
            yield f"\n[错误] 调用失败：{message}\n"
            return

        chunk = _extract_content(response)
        if chunk:
            yield chunk
