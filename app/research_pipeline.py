import glob
import io
import os
import re
from dataclasses import dataclass
from typing import List, Optional

import requests
from pypdf import PdfReader

from app.crypto_client import get_crypto_snapshot, get_crypto_chart_data
from app.news_client import get_crypto_news
from app.search_client import search_web
from app.config import LOCAL_PDF_DIR, MAX_PDF_FILES, MAX_PDF_PAGES


@dataclass
class SourceItem:
    title: str
    url: str
    snippet: str


@dataclass
class ResearchInput:
    question: str
    pdf_urls: List[str]


@dataclass
class ResearchOutput:
    sources: List[SourceItem]
    extracted_text: str
    crypto_context: str
    news_context: str
    search_context: str
    chart_data: dict


def _fetch_pdf_text(source: str, max_pages: int = 6) -> str:
    if os.path.exists(source):
        try:
            reader = PdfReader(source)
        except Exception:
            return ""
    else:
        try:
            resp = requests.get(source, timeout=12)
            resp.raise_for_status()
        except Exception:
            return ""

        try:
            reader = PdfReader(io.BytesIO(resp.content))
        except Exception:
            return ""

    parts: List[str] = []
    for i, page in enumerate(reader.pages):
        if i >= max_pages:
            break
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text.strip():
            parts.append(text.strip())
    return "\n".join(parts)


def collect_pdf_text(urls: List[str]) -> str:
    chunks: List[str] = []
    for url in urls:
        text = _fetch_pdf_text(url, max_pages=MAX_PDF_PAGES)
        if text:
            chunks.append(f"[PDF] {url}\n{text}")
    return "\n\n".join(chunks)


def collect_local_pdfs() -> List[str]:
    if not LOCAL_PDF_DIR or not os.path.isdir(LOCAL_PDF_DIR):
        return []
    paths = sorted(glob.glob(os.path.join(LOCAL_PDF_DIR, "*.pdf")))
    return paths[:MAX_PDF_FILES]


def extract_urls(text: str) -> List[str]:
    if not text:
        return []
    urls = re.findall(r"https?://[^\s]+", text)
    return list(dict.fromkeys(urls))


def run_research(question: str, pdf_urls: Optional[List[str]] = None) -> ResearchOutput:
    pdf_urls = pdf_urls or []

    web_results = search_web(question, max_results=5)
    sources = [SourceItem(**item) for item in web_results]

    auto_pdf_urls = [
        item["url"] for item in web_results if ".pdf" in item["url"].lower()
    ]
    local_pdfs = collect_local_pdfs()

    merged_pdf_urls = list(dict.fromkeys(pdf_urls + auto_pdf_urls + local_pdfs))
    pdf_text = collect_pdf_text(merged_pdf_urls)

    crypto_context = get_crypto_snapshot(question)
    news_context = get_crypto_news(question)
    chart_data = get_crypto_chart_data(question)

    search_context = ""
    if web_results:
        lines = ["搜索结果（标题列表）："]
        for item in web_results:
            lines.append(f"- {item['title']} ({item['url']})")
        search_context = "\n".join(lines)

    for url in merged_pdf_urls:
        if url not in [s.url for s in sources]:
            sources.append(SourceItem(title="PDF", url=url, snippet="PDF内容已提取"))

    return ResearchOutput(
        sources=sources,
        extracted_text=pdf_text,
        crypto_context=crypto_context,
        news_context=news_context,
        search_context=search_context,
        chart_data=chart_data,
    )
