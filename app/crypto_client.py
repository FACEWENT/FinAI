import re
from datetime import datetime, timedelta
from typing import Optional

import requests

COINCAP_BASE = "https://api.coincap.io/v2"

_SYMBOL_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binance-coin",
    "XRP": "xrp",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "LINK": "chainlink",
    "LTC": "litecoin",
    "AVAX": "avalanche",
    "MATIC": "polygon",
    "TON": "toncoin",
    "TRX": "tron",
    "BCH": "bitcoin-cash",
}


def _extract_symbol(text: str) -> Optional[str]:
    match = re.search(r"(?:\\$)?([A-Z]{2,6})", text.upper())
    if not match:
        return None
    symbol = match.group(1)
    return symbol if symbol in _SYMBOL_MAP else None


def _resolve_asset_id(symbol: str) -> Optional[str]:
    if symbol in _SYMBOL_MAP:
        return _SYMBOL_MAP[symbol]

    try:
        resp = requests.get(f"{COINCAP_BASE}/assets", params={"search": symbol}, timeout=6)
        resp.raise_for_status()
        data = resp.json().get("data") or []
    except Exception:
        return None

    for item in data:
        if str(item.get("symbol", "")).upper() == symbol:
            return item.get("id")
    return data[0].get("id") if data else None


def _get_asset_id_from_question(question: str) -> Optional[tuple[str, str]]:
    symbol = _extract_symbol(question)
    if not symbol:
        return None
    asset_id = _resolve_asset_id(symbol)
    if not asset_id:
        return None
    return symbol, asset_id


def get_crypto_snapshot(question: str) -> str:
    resolved = _get_asset_id_from_question(question)
    if not resolved:
        return ""
    symbol, asset_id = resolved

    try:
        resp = requests.get(f"{COINCAP_BASE}/assets/{asset_id}", timeout=6)
        resp.raise_for_status()
        data = resp.json().get("data") or {}
    except Exception:
        return ""

    try:
        price = float(data.get("priceUsd"))
        change_24h = float(data.get("changePercent24Hr"))
        mcap = float(data.get("marketCapUsd"))
        vol = float(data.get("volumeUsd24Hr"))
    except Exception:
        return ""

    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"CoinCap 行情数据（{symbol}）\\n"
        f"时间：{ts}\\n"
        f"价格：${price:,.2f}\\n"
        f"24H涨跌：{change_24h:.2f}%\\n"
        f"市值：${mcap:,.0f}\\n"
        f"24H成交量：${vol:,.0f}"
    )


def get_crypto_chart_data(question: str, days: int = 30) -> dict:
    resolved = _get_asset_id_from_question(question)
    if not resolved:
        return {}
    symbol, asset_id = resolved

    end = datetime.utcnow()
    start = end - timedelta(days=days)
    params = {
        "interval": "d1",
        "start": int(start.timestamp() * 1000),
        "end": int(end.timestamp() * 1000),
    }
    try:
        resp = requests.get(
            f"{COINCAP_BASE}/assets/{asset_id}/history",
            params=params,
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json().get("data") or []
    except Exception:
        return {}

    labels = []
    prices = []
    for item in data:
        try:
            dt = datetime.fromtimestamp(item.get("time") / 1000)
            price = float(item.get("priceUsd"))
        except Exception:
            continue
        labels.append(dt.strftime("%m-%d"))
        prices.append(round(price, 2))

    snapshot = _get_snapshot_metrics(asset_id)
    return {
        "symbol": symbol,
        "line": {"labels": labels, "values": prices},
        "bars": snapshot,
    }


def _get_snapshot_metrics(asset_id: str) -> dict:
    try:
        resp = requests.get(f"{COINCAP_BASE}/assets/{asset_id}", timeout=6)
        resp.raise_for_status()
        data = resp.json().get("data") or {}
        mcap = float(data.get("marketCapUsd"))
        vol = float(data.get("volumeUsd24Hr"))
    except Exception:
        return {}
    return {"marketCapUsd": round(mcap, 0), "volumeUsd24Hr": round(vol, 0)}
