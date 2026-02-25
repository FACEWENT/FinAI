import re
from datetime import datetime
from typing import List, Optional
from xml.etree import ElementTree as ET

import requests

from app.config import CHAIN_GPT_RSS_URL


def _extract_symbol(text: str) -> Optional[str]:
    match = re.search(r"(?:\\$)?([A-Z]{2,6})", text.upper())
    if not match:
        return None
    return match.group(1)


def _parse_rss_items(xml_text: str) -> List[dict]:
    items = []
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return items

    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        if title:
            items.append({"title": title, "link": link, "pub_date": pub_date})
    return items


def get_crypto_news(question: str, limit: int = 3) -> str:
    if not CHAIN_GPT_RSS_URL:
        return ""

    try:
        resp = requests.get(CHAIN_GPT_RSS_URL, timeout=8)
        resp.raise_for_status()
    except Exception:
        return ""

    items = _parse_rss_items(resp.text)
    if not items:
        return ""

    symbol = _extract_symbol(question)
    if symbol:
        filtered = [it for it in items if symbol in it["title"].upper()]
        items = filtered or items

    lines = ["最新加密货币资讯（ChainGPT RSS）"]
    for it in items[:limit]:
        title = it["title"]
        pub_date = it["pub_date"]
        if pub_date:
            try:
                pub_dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
                pub_date = pub_dt.strftime("%Y-%m-%d %H:%M %Z")
            except Exception:
                pass
        if pub_date:
            lines.append(f"- {title}（{pub_date}）")
        else:
            lines.append(f"- {title}")

    return "\n".join(lines)
