# -*- coding: utf-8 -*-
"""Quasi-realtime quote snapshots for report references.

This module is for observation and report citation only. It does not provide
trade execution, order routing, or zero-latency market data.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import pandas as pd
import requests
import yfinance as yf


@dataclass(frozen=True)
class QuoteSnapshot:
    symbol: str
    market: str
    name: str
    price: float | None
    change_pct: float | None
    volume: float | None
    quote_time: str | None
    retrieved_at: str
    source: str
    reliability: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def fetch_realtime_quote(symbol: str, market: str) -> QuoteSnapshot:
    market = (market or "").lower()
    if market == "a_stock":
        return fetch_a_stock_spot(symbol)
    if market == "fund":
        return fetch_fund_estimate(symbol)
    if market in {"us_stock", "crypto"}:
        return fetch_yfinance_spot(symbol, market)
    raise ValueError(f"Unsupported realtime market: {market}")


def fetch_a_stock_spot(symbol: str) -> QuoteSnapshot:
    import akshare as ak

    requested = normalize_a_symbol(symbol)
    df = ak.stock_zh_a_spot_em()
    code_col = pick_column(df, ["代码", "code"])
    if code_col is None:
        raise RuntimeError("AkShare spot data missing stock code column.")
    rows = df[df[code_col].astype(str).str.zfill(6) == requested]
    if rows.empty:
        raise RuntimeError(f"AkShare spot data does not contain {symbol}.")
    row = rows.iloc[0]
    return QuoteSnapshot(
        symbol=requested,
        market="a_stock",
        name=str(value_from(row, ["名称", "name"], "")),
        price=to_float(value_from(row, ["最新价", "最新", "price"], None)),
        change_pct=to_float(value_from(row, ["涨跌幅", "change_pct"], None)),
        volume=to_float(value_from(row, ["成交量", "volume"], None)),
        quote_time=str(value_from(row, ["更新时间", "时间", "quote_time"], "")) or None,
        retrieved_at=now_text(),
        source="AkShare / 东方财富实时行情",
        reliability="medium",
        notes="准实时行情快照，可能存在延迟，仅用于报告引用、观察和风险预警，不作为交易指令。",
    )


def fetch_yfinance_spot(symbol: str, market: str) -> QuoteSnapshot:
    ticker = yf.Ticker(symbol)
    last_error: Exception | None = None
    df = pd.DataFrame()
    for period, interval in [("1d", "1m"), ("5d", "5m"), ("1mo", "1d")]:
        try:
            df = ticker.history(period=period, interval=interval)
            if df is not None and not df.empty:
                break
        except Exception as exc:
            last_error = exc
            time.sleep(0.5)
    if df is None or df.empty:
        raise RuntimeError(f"yfinance quote unavailable for {symbol}: {last_error}")
    row = df.dropna(how="all").iloc[-1]
    quote_time = df.dropna(how="all").index[-1]
    if hasattr(quote_time, "tz_localize"):
        try:
            quote_time = quote_time.tz_localize(None)
        except TypeError:
            quote_time = quote_time.tz_convert(None)
    return QuoteSnapshot(
        symbol=symbol,
        market=market,
        name=symbol,
        price=to_float(row.get("Close")),
        change_pct=None,
        volume=to_float(row.get("Volume")),
        quote_time=str(quote_time),
        retrieved_at=now_text(),
        source="yfinance",
        reliability="medium",
        notes="yfinance 分钟/日线准实时快照可能延迟或限流，仅用于报告观察引用。",
    )


def fetch_fund_estimate(fund_code: str) -> QuoteSnapshot:
    """Fetch an Eastmoney fund estimate/latest NAV style snapshot.

    Eastmoney field availability varies. For OTC funds this is not a traded
    realtime price; it is a NAV/estimate reference.
    """

    code = str(fund_code).strip()
    url = (
        "https://fundgz.1234567.com.cn/js/"
        f"{code}.js?rt={int(time.time() * 1000)}"
    )
    session = requests.Session()
    session.trust_env = False
    resp = session.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": f"https://fund.eastmoney.com/{code}.html",
        },
        timeout=8,
    )
    resp.raise_for_status()
    text = resp.text.strip()
    payload = parse_eastmoney_jsonp(text)
    return QuoteSnapshot(
        symbol=code,
        market="fund",
        name=str(payload.get("name") or payload.get("fundcode") or code),
        price=to_float(payload.get("gsz") or payload.get("dwjz")),
        change_pct=to_float(payload.get("gszzl")),
        volume=None,
        quote_time=str(payload.get("gztime") or payload.get("jzrq") or "") or None,
        retrieved_at=now_text(),
        source="东方财富基金估算接口",
        reliability="medium",
        notes="场外基金不是盘中连续成交品种；该值为净值/估算参考，仅用于报告背景和观察。",
    )


def parse_eastmoney_jsonp(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise RuntimeError("Eastmoney response is not JSONP.")
    import json

    return json.loads(text[start : end + 1])


def normalize_a_symbol(symbol: str) -> str:
    return "".join(ch for ch in str(symbol) if ch.isdigit()).zfill(6)


def pick_column(df: pd.DataFrame, names: list[str]) -> str | None:
    normalized = {str(col).lower(): col for col in df.columns}
    for name in names:
        found = normalized.get(name.lower())
        if found is not None:
            return found
    return None


def value_from(row: pd.Series, names: list[str], default: Any) -> Any:
    for name in names:
        if name in row.index:
            return row.get(name, default)
    lower = {str(idx).lower(): idx for idx in row.index}
    for name in names:
        idx = lower.get(name.lower())
        if idx is not None:
            return row.get(idx, default)
    return default


def to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        result = float(value)
        if pd.isna(result):
            return None
        return result
    except Exception:
        return None


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
