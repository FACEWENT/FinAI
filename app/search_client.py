import html
import re
from typing import List
from urllib.parse import parse_qs, unquote, urlparse

import requests


def _normalize_duckduckgo_url(url: str) -> str:
    # DuckDuckGo may wrap URLs via /l/?uddg=
    if "duckduckgo.com/l/?" not in url:
        return url
    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    except Exception:
        return url
    return url


def search_web(query: str, max_results: int = 5) -> List[dict]:
    if not query:
        return []

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(
            "https://duckduckgo.com/html/",
            params={"q": query},
            headers=headers,
            timeout=8,
        )
        resp.raise_for_status()
    except Exception:
        return []

    results = []
    pattern = re.compile(r'<a[^>]+class=\"result__a\"[^>]+href=\"([^\"]+)\"[^>]*>(.*?)</a>')
    for url, title in pattern.findall(resp.text):
        clean_title = html.unescape(re.sub(r"<.*?>", "", title)).strip()
        clean_url = _normalize_duckduckgo_url(html.unescape(url))
        if not clean_title or not clean_url:
            continue
        results.append({"title": clean_title, "url": clean_url, "snippet": ""})
        if len(results) >= max_results:
            break

    return results
