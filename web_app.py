#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import json
import logging
import os
import re
import secrets
import shutil
import sys
import traceback
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from functools import lru_cache
from logging.handlers import RotatingFileHandler
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, redirect, render_template_string, request, send_from_directory, session, url_for

from agent.quant_agent import QuantAgent
from core.broker_adapter import BrokerAdapter
from core.indicators import add_all_indicators, generate_signal_summary
from core.value_analysis import fetch_stock_value, format_value_report
from reports.visualizer import ReportVisualizer
from web_modules.templates import PAGE_TEMPLATE


BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
DATA_DIR = BASE_DIR / "data"
USERSPACE_DIR = DATA_DIR / "userspace"
SESSION_SECRET_FILE = DATA_DIR / ".session_secret"
LOGS_DIR = BASE_DIR / "logs"

app = Flask(__name__)

INDEX_SYMBOL_NAMES = {
    "沪深300": "000300",
    "中证500": "000905",
    "上证50": "000016",
    "中证1000": "000852",
}
INDEX_SYMBOLS = set(INDEX_SYMBOL_NAMES.values())
FUND_SYMBOL_NAMES = {
    "广发纯债债券A": "270048",
    "广发纳斯达克100ETF联接人民币(QDII)C": "006479",
}
INDEX_CODE_NAMES = {code: name for name, code in INDEX_SYMBOL_NAMES.items()}
FUND_CODE_NAMES = {code: name for name, code in FUND_SYMBOL_NAMES.items()}
MARKET_LABELS = {
    "auto": "自动识别",
    "fund": "基金",
    "a_stock": "A股/指数",
    "us_stock": "美股",
    "crypto": "数字资产",
}
STOCK_CODE_PREFIXES = ("000", "001", "002", "003", "300", "301", "600", "601", "603", "605", "688", "689")
CN_INDEX_PROXY_SYMBOLS = {
    "000300": "沪深300",
    "000905": "中证500",
    "000016": "上证50",
    "000852": "中证1000",
}
FUND_VALUATION_PROXIES = (
    ("沪深300价值", ("cn-index", "沪深300")),
    ("沪深300", ("cn-index", "沪深300")),
    ("中证500", ("cn-index", "中证500")),
    ("上证50", ("cn-index", "上证50")),
    ("中证1000", ("cn-index", "中证1000")),
    ("红利低波", ("cn-index", "上证红利")),
    ("纳斯达克100", ("us-etf", "QQQ")),
    ("NASDAQ 100", ("us-etf", "QQQ")),
    ("港股通互联网", ("us-etf", "PGJ")),
)


def _broker_data_ready() -> bool:
    return broker_adapter.ready


def _broker_data_source_label() -> str:
    return broker_adapter.label


def _load_secret_key() -> str:
    env_secret = os.getenv("FLASK_SECRET_KEY") or os.getenv("SECRET_KEY")
    if env_secret:
        return env_secret
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if SESSION_SECRET_FILE.exists():
        secret = SESSION_SECRET_FILE.read_text(encoding="utf-8").strip()
        if secret:
            return secret
    secret = secrets.token_hex(32)
    SESSION_SECRET_FILE.write_text(secret, encoding="utf-8")
    return secret


app.secret_key = _load_secret_key()
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,
)

LOGS_DIR.mkdir(parents=True, exist_ok=True)
file_handler = RotatingFileHandler(LOGS_DIR / "web_app.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

agent = QuantAgent(config_path=str(BASE_DIR / "config.yaml"), paper_trade=False)
broker_adapter = BrokerAdapter.from_config(agent.config.get("broker", {}))
visualizer = ReportVisualizer(output_dir=str(REPORTS_DIR))


def _csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = uuid4().hex + uuid4().hex
        session["csrf_token"] = token
    return token


def _csrf_input() -> str:
    return f'<input type="hidden" name="csrf_token" value="{_csrf_token()}">'


def _inject_csrf_fields(html: str) -> str:
    token_field = str(_csrf_input())
    html = re.sub(r"(<form\b[^>]*method=[\"']post[\"'][^>]*>)", r"\1" + token_field, html, flags=re.IGNORECASE)
    html = re.sub(r"(<form\b[^>]*method=post\b[^>]*>)", r"\1" + token_field, html, flags=re.IGNORECASE)
    return html


@app.context_processor
def _template_helpers() -> dict:
    return {"csrf_token": _csrf_token, "csrf_input": _csrf_input}


@app.before_request
def _protect_post_requests():
    if request.method != "POST":
        return None
    expected = session.get("csrf_token") or _csrf_token()
    supplied = request.form.get("csrf_token", "") or request.headers.get("X-CSRF-Token", "")
    if not supplied or supplied != expected:
        return "CSRF validation failed", 400
    return None


@app.after_request
def _add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    if response.content_type and response.content_type.startswith("text/html"):
        try:
            response.set_data(_inject_csrf_fields(response.get_data(as_text=True)))
        except Exception:
            pass
    return response


def _safe_username(username: str | None) -> str:
    base = (username or "guest").strip()
    base = re.sub(r"[^0-9A-Za-z_\-]+", "_", base)
    return base or "guest"


def _current_user() -> str:
    return _safe_username(session.get("username") or "guest")


def _user_dir(username: str | None = None) -> Path:
    path = USERSPACE_DIR / _safe_username(username or _current_user())
    path.mkdir(parents=True, exist_ok=True)
    return path


def _user_file(username: str | None, name: str) -> Path:
    return _user_dir(username) / name


def _read_json_file(path: Path, default):
    if not path.exists():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data
    except Exception:
        return default


def _write_json_file(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _default_form() -> dict:
    return {
        "prompt": "",
        "symbol": "002982",
        "market": "auto",
        "period": "max",
        "start_date": "",
        "end_date": "",
        "use_ai": False,
        "reader_version": "个人投资者版",
    }


def _normalize_market(value: str | None) -> str:
    market = (value or "auto").strip()
    return market if market in {"auto", "fund", "a_stock", "us_stock", "crypto"} else "auto"


def _normalize_period(value: str | None) -> str:
    period = (value or "max").strip()
    allowed = {"1mo", "3mo", "6mo", "1y", "2y", "3y", "5y", "10y", "20y", "50y", "max"}
    return period if period in allowed else "max"


def _normalize_symbol(symbol: str, market: str) -> str:
    symbol = (symbol or "").strip()
    if market in ("auto", "fund", "a_stock") and symbol.isdigit():
        return symbol.zfill(6)
    return symbol.upper() if market in ("us_stock", "crypto") else symbol


def _resolve_search_symbol(symbol: str, market: str) -> tuple[str, str]:
    raw = (symbol or "").strip()
    if raw in INDEX_SYMBOL_NAMES:
        return INDEX_SYMBOL_NAMES[raw], "a_stock"
    if raw in FUND_SYMBOL_NAMES:
        return FUND_SYMBOL_NAMES[raw], "fund"
    normalized = _normalize_symbol(raw, market)
    if normalized in INDEX_SYMBOLS:
        return normalized, "a_stock"
    if market == "auto":
        if normalized.isdigit() and len(normalized) == 6:
            return normalized, "a_stock" if normalized.startswith(STOCK_CODE_PREFIXES) else "fund"
        if re.fullmatch(r"[A-Za-z]{1,10}(?:[-.][A-Za-z]{1,10})?", normalized):
            return normalized, "us_stock"
    return normalized, market


def _safe_float(value, digits: int = 4) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    if number != number:
        return "-"
    return f"{number:.{digits}f}"


def _safe_pct(value, digits: int = 2) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    if number != number:
        return "-"
    return f"{number * 100:.{digits}f}%"


def _display_percent(value, digits: int = 2) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if number != number:
        return ""
    if abs(number) < 1:
        number *= 100
    return f"{number:.{digits}f}%"


def _display_ratio(value, digits: int = 2) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if number != number:
        return ""
    return f"{number:.{digits}f}"


def _display_security_name(symbol: str, market: str, valuation: dict | None = None) -> str:
    valuation = valuation or {}
    name = (valuation.get("name") or "").strip()
    if name and name != symbol:
        return name
    if market == "a_stock" and symbol in INDEX_CODE_NAMES:
        return INDEX_CODE_NAMES[symbol]
    if market == "fund" and symbol in FUND_CODE_NAMES:
        return FUND_CODE_NAMES[symbol]
    return symbol


@lru_cache(maxsize=32)
def _fetch_cn_index_proxy(index_name: str) -> dict:
    try:
        import akshare as ak

        pe_df = ak.stock_index_pe_lg(symbol=index_name)
        pb_df = ak.stock_index_pb_lg(symbol=index_name)
        pe_value = None
        pb_value = None
        if pe_df is not None and not pe_df.empty:
            latest = pe_df.iloc[-1]
            pe_value = latest.get("滚动市盈率") or latest.get("静态市盈率")
        if pb_df is not None and not pb_df.empty:
            latest = pb_df.iloc[-1]
            pb_value = latest.get("市净率")
        return {
            "pe": _display_ratio(pe_value),
            "pb": _display_ratio(pb_value),
            "source": f"{index_name}指数估值",
        }
    except Exception:
        return {"pe": "", "pb": "", "source": ""}


@lru_cache(maxsize=16)
def _fetch_us_etf_proxy(ticker: str) -> dict:
    try:
        import yfinance as yf

        info = yf.Ticker(ticker).info or {}
        pe_value = info.get("trailingPE") or info.get("forwardPE")
        pb_value = info.get("priceToBook")
        short_name = info.get("shortName") or ticker
        return {
            "pe": _display_ratio(pe_value),
            "pb": _display_ratio(pb_value),
            "source": f"{short_name}代理估值",
        }
    except Exception:
        return {"pe": "", "pb": "", "source": ""}


def _infer_proxy_valuation(symbol: str, market: str, valuation: dict | None = None) -> dict:
    valuation = valuation or {}
    name = _display_security_name(symbol, market, valuation)
    if market == "a_stock" and symbol in CN_INDEX_PROXY_SYMBOLS:
        return _fetch_cn_index_proxy(CN_INDEX_PROXY_SYMBOLS[symbol])
    if market == "fund":
        upper_name = name.upper()
        for keyword, (proxy_type, proxy_symbol) in FUND_VALUATION_PROXIES:
            matched = keyword in upper_name if keyword.isascii() else keyword in name
            if not matched:
                continue
            if proxy_type == "cn-index":
                return _fetch_cn_index_proxy(proxy_symbol)
            if proxy_type == "us-etf":
                return _fetch_us_etf_proxy(proxy_symbol)
    return {"pe": "", "pb": "", "source": ""}


def _watchlist_valuation_payload(symbol: str, market: str, valuation: dict | None, summary: dict | None = None) -> dict:
    valuation = valuation or {}
    summary = summary or {}
    pe_raw = valuation.get("pe_trailing") or valuation.get("pe_forward") or valuation.get("pe")
    pb_raw = valuation.get("pb")
    dividend_raw = valuation.get("dividend_yield")
    roe_raw = valuation.get("roe")
    pe = _display_ratio(pe_raw)
    pb = _display_ratio(pb_raw)
    valuation_note = ""
    if not pe or not pb:
        proxy = _infer_proxy_valuation(symbol, market, valuation)
        if not pe:
            pe = proxy.get("pe", "")
        if not pb:
            pb = proxy.get("pb", "")
        valuation_note = proxy.get("source", "")
    dividend = _display_percent(dividend_raw)
    roe = _display_percent(roe_raw)
    earnings_yield = ""
    try:
        pe_number = float(pe_raw)
        if pe_number > 0:
            earnings_yield = f"{100 / pe_number:.2f}%"
    except (TypeError, ValueError):
        pass

    def _parse_percent(value: str | None):
        if value in (None, "", "-"):
            return None
        try:
            return float(str(value).replace("%", "").strip())
        except ValueError:
            return None

    def _market_observation() -> tuple[str, str]:
        rsi_value = _parse_percent(summary.get("rsi"))
        position_value = _parse_percent(summary.get("position"))
        drawdown_value = _parse_percent(summary.get("drawdown"))
        ma20_value = summary.get("ma20")
        ma60_value = summary.get("ma60")

        try:
            ma20_num = float(ma20_value)
            ma60_num = float(ma60_value)
        except (TypeError, ValueError):
            ma20_num = ma60_num = None

        if rsi_value is not None and rsi_value <= 30:
            return "接近超卖", "status-high"
        if rsi_value is not None and rsi_value >= 70:
            return "短线过热", "status-high"
        if drawdown_value is not None and drawdown_value <= -10:
            return "回撤较深", "status-high"
        if position_value is not None and position_value >= 80 and drawdown_value is not None and drawdown_value < 0:
            return "高位回撤", "status-normal"
        if position_value is not None and position_value <= 20:
            return "低位观察", "status-low"
        if ma20_num is not None and ma60_num is not None:
            if ma20_num > ma60_num:
                return "趋势偏强", "status-low"
            if ma20_num < ma60_num:
                return "趋势偏弱", "status-normal"
        return "温和观察", "status-normal"

    has_stock_metrics = any((pe, pb, dividend, roe))
    is_index = market == "a_stock" and symbol in INDEX_SYMBOLS
    if has_stock_metrics:
        conclusion = "待复核"
        status = "status-normal"
        stars = "★★★☆☆"
        metric_mode = "valuation"
        try:
            pe_number = float(pe_raw)
            if pe_number > 0 and pe_number <= 15:
                conclusion, status, stars = "估值偏低", "status-low", "★★★★☆"
            elif pe_number >= 35:
                conclusion, status, stars = "估值偏高", "status-high", "★★☆☆☆"
        except (TypeError, ValueError):
            pass
        source = "structured-valuation"
    else:
        if market in ("fund", "a_stock"):
            conclusion, status = _market_observation()
        else:
            conclusion, status = "数据不足", "status-normal"
        stars = ""
        source = "market-summary"
        metric_mode = "market"

    latest_value = (summary.get("buy_rows") or [{}])[0].get("value", "") if summary.get("buy_rows") else ""
    latest_value_note = summary.get("data_end_note", "")
    is_stale_market_data = bool(summary.get("is_stale_market_data"))

    return {
        "symbol": symbol,
        "market": market,
        "metricMode": metric_mode,
        "name": _display_security_name(symbol, market, valuation),
        "status": "status-normal" if (metric_mode == "market" and is_stale_market_data) else status,
        "conclusion": "数据待更新" if (metric_mode == "market" and is_stale_market_data) else conclusion,
        "stars": stars,
        "earningsYield": earnings_yield,
        "pe": pe,
        "pb": pb,
        "valuationNote": valuation_note,
        "dividend": dividend,
        "roe": roe,
        "latestValue": latest_value,
        "latestValueNote": latest_value_note,
        "isStaleMarketData": is_stale_market_data,
        "position": summary.get("position", ""),
        "drawdown": summary.get("drawdown", ""),
        "rsi": summary.get("rsi", ""),
        "ma20": summary.get("ma20", ""),
        "ma60": summary.get("ma60", ""),
        "exchangeFund": symbol if market != "fund" else "",
        "offExchangeFund": symbol if market == "fund" else "",
        "valuationSource": source,
    }


def _json_number(value, digits: int = 4):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return round(number, digits)


def _result_unit_label(market: str, symbol: str) -> str:
    if market == "fund":
        return "单位净值"
    if market == "a_stock" and symbol in INDEX_SYMBOLS:
        return "当前点数"
    return "当前价格"


def _is_stale_date(date_text: str, max_age_days: int = 45) -> bool:
    try:
        data_date = datetime.strptime(date_text, "%Y-%m-%d")
    except (TypeError, ValueError):
        return False
    return data_date < datetime.now() - timedelta(days=max_age_days)


def _is_market_data_stale(date_text: str, max_age_days: int = 3) -> bool:
    try:
        data_date = datetime.strptime(date_text, "%Y-%m-%d")
    except (TypeError, ValueError):
        return False
    return data_date < datetime.now() - timedelta(days=max_age_days)


def _display_unit_label(market: str, symbol: str, data_end: str | None = None) -> str:
    label = _result_unit_label(market, symbol)
    if data_end and _is_stale_date(data_end):
        return f"最后{label}"
    return label


def _build_search_summary(result: dict, df) -> dict:
    symbol = result.get("symbol", "")
    market = result.get("market", "")
    latest = df.iloc[-1] if df is not None and not df.empty else {}
    prev = df.iloc[-2] if df is not None and len(df) > 1 else latest
    close = latest.get("close", "")
    prev_close = prev.get("close", "")
    change_pct = ""
    try:
        change_pct = (float(close) / float(prev_close) - 1) if float(prev_close) else ""
    except (TypeError, ValueError, ZeroDivisionError):
        change_pct = ""

    ma20 = latest.get("MA20", "")
    ma60 = latest.get("MA60", "")
    rsi = latest.get("RSI", "")
    recent = df.tail(min(len(df), 252)) if df is not None and not df.empty else df
    high_252 = recent["close"].max() if recent is not None and not recent.empty else ""
    low_252 = recent["close"].min() if recent is not None and not recent.empty else ""
    drawdown = ""
    position = ""
    try:
        close_float = float(close)
        high_float = float(high_252)
        low_float = float(low_252)
        drawdown = close_float / high_float - 1 if high_float else ""
        position = (close_float - low_float) / (high_float - low_float) if high_float != low_float else ""
    except (TypeError, ValueError, ZeroDivisionError):
        pass

    if result.get("backtest") and getattr(result["backtest"], "total_return", None) is not None:
        strategy_return = result["backtest"].total_return
    else:
        strategy_return = ""
    if result.get("benchmark") and getattr(result["benchmark"], "total_return", None) is not None:
        benchmark_return = result["benchmark"].total_return
    else:
        benchmark_return = ""

    signal = result.get("signals", {})
    data_end = df.index.max().strftime("%Y-%m-%d") if df is not None and not df.empty else ""
    unit_label = _display_unit_label(market, symbol, data_end)
    is_stale_market_data = bool(data_end and _is_market_data_stale(data_end))
    stale_note = f"该标的最近数据截止 {data_end}，可能已终止、退市或数据源不再更新。" if data_end and _is_stale_date(data_end) else ""
    data_end_note = f"截至 {data_end}" if data_end else ""
    buy_rows = [
        {"label": "当前值", "value": _safe_float(close), "note": unit_label},
        {"label": "日变化", "value": _safe_pct(change_pct), "note": "最近两个交易日"},
        {"label": "20日均线", "value": _safe_float(ma20), "note": "短中期趋势"},
        {"label": "60日均线", "value": _safe_float(ma60), "note": "中期参照"},
        {"label": "RSI", "value": _safe_float(rsi, 2), "note": "情绪温度"},
        {"label": "近一年位置", "value": _safe_pct(position), "note": "越高越接近年内高位"},
        {"label": "距近一年高点", "value": _safe_pct(drawdown), "note": "回撤幅度"},
        {"label": "示例回测", "value": _safe_pct(strategy_return), "note": "均线规则，仅供复盘"},
        {"label": "同期持有", "value": _safe_pct(benchmark_return), "note": "同区间参照"},
    ]
    if stale_note:
        evidence_note = stale_note
    elif data_end:
        evidence_note = f"图表已按本次获取的数据重绘，最后一条行情为 {data_end}。"
    else:
        evidence_note = "当前没有可用行情，先检查代码、市场类型或数据源。"
    return {
        "unit_label": unit_label,
        "market_label": MARKET_LABELS.get(market, market),
        "change_pct": _safe_pct(change_pct),
        "ma20": _safe_float(ma20),
        "ma60": _safe_float(ma60),
        "rsi": _safe_float(rsi, 2),
        "position": _safe_pct(position),
        "drawdown": _safe_pct(drawdown),
        "signal_text": "；".join(f"{k}: {v}" for k, v in signal.items()) or "暂无信号",
        "stale_note": stale_note,
        "is_stale_market_data": is_stale_market_data,
        "data_end": data_end,
        "data_end_note": data_end_note,
        "evidence_note": evidence_note,
        "buy_rows": buy_rows,
    }


def _normalize_backtest_date(value: str | None, field_name: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"{field_name}必须是 YYYY-MM-DD 格式。") from exc


def _friendly_error(exc: Exception) -> str:
    message = str(exc).strip() or "操作失败"
    if any(key in message for key in ("ProxyError", "Max retries exceeded", "HTTPSConnectionPool", "Unable to connect")):
        return "数据源连接失败，通常是临时网络或代理问题。"
    return f"操作失败：{message}"


def _read_history(username: str | None = None, limit: int = 20) -> list[dict]:
    data = _read_json_file(_user_file(username, "analysis_history.json"), [])
    return data[:limit] if isinstance(data, list) else []


def _write_history_item(item: dict, username: str | None = None, limit: int = 50) -> None:
    item = dict(item)
    item["username"] = _safe_username(username or _current_user())
    history = _read_history(username=username, limit=limit)
    deduped = [
        old for old in history
        if not (
            old.get("symbol") == item.get("symbol")
            and old.get("market") == item.get("market")
            and old.get("period") == item.get("period")
            and old.get("use_ai") == item.get("use_ai")
        )
    ]
    _write_json_file(_user_file(username, "analysis_history.json"), [item, *deduped][:limit])


def _to_image_url(path_str: str | None) -> str | None:
    if not path_str:
        return None
    path = Path(path_str)
    try:
        rel_name = path.relative_to(REPORTS_DIR).as_posix()
    except ValueError:
        rel_name = path.name
    return url_for("serve_report", filename=rel_name)


def _validate_curve_points(points: list[dict], initial_cash: float, total_return: float, label: str) -> None:
    if not points:
        raise RuntimeError(f"{label} curve is empty.")
    first = points[0]["value"]
    last = points[-1]["value"]
    if abs(first - initial_cash) > max(1.0, initial_cash * 0.001):
        raise RuntimeError(f"{label} curve starts from an unexpected value: {first}")
    expected_last = initial_cash * (1 + total_return)
    if abs(last - expected_last) > max(1.0, abs(expected_last) * 0.001):
        raise RuntimeError(f"{label} curve does not match backtest return.")


def _stock_fundamental_fallback(symbol: str, market: str, period: str, error: Exception, use_ai: bool, username: str | None = None) -> dict:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        print("Market price data is temporarily unavailable; using fundamental fallback mode.")
        print(f"Reason: {_friendly_error(error)}")
        val_data = None
        try:
            val_data = fetch_stock_value(symbol, market)
        except Exception:
            val_data = None
        if val_data:
            print(format_value_report(val_data))
        else:
            print(format_value_report({"market": market, "symbol": symbol, "name": symbol}))
        print(agent._format_cross_asset_valuation(market, val_data))
        print("Technical chart and backtest are unavailable until market data recovers.")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    analysis_result = {
        "symbol": symbol,
        "market": market,
        "market_label": MARKET_LABELS.get(market, market),
        "unit_label": _result_unit_label(market, symbol),
        "period": period,
        "latest_price": "",
        "data_range": "market data unavailable",
        "data_points": 0,
        "generated_at": now,
        "log": buffer.getvalue(),
        "analysis_image": None,
        "equity_image": None,
        "equity_points": [],
        "benchmark_points": [],
        "history_points": [],
        "valuation": val_data or {},
        "display_name": _display_security_name(symbol, market, val_data),
        "summary": {
            "unit_label": _result_unit_label(market, symbol),
            "market_label": MARKET_LABELS.get(market, market),
            "change_pct": "-",
            "ma20": "-",
            "ma60": "-",
            "rsi": "-",
            "position": "-",
            "drawdown": "-",
            "signal_text": "价格数据暂不可用",
            "stale_note": "",
            "buy_rows": [],
        },
    }
    analysis_result["watchlist_item"] = _watchlist_valuation_payload(symbol, market, val_data, analysis_result["summary"])
    _write_history_item({
        "time": now[:16],
        "symbol": symbol,
        "market": market,
        "period": period,
        "use_ai": bool(use_ai),
        "latest_price": "-",
        "data_range": analysis_result["data_range"],
        "data_points": 0,
        "analysis_image": None,
    }, username=username)
    return analysis_result


def _run_analysis(
    symbol: str,
    market: str,
    period: str,
    use_ai: bool,
    force_refresh: bool = False,
    username: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    username = username or _current_user()
    buffer = io.StringIO()
    equity_points: list[dict] = []
    benchmark_points: list[dict] = []
    history_points: list[dict] = []
    analysis_path = None
    with redirect_stdout(buffer):
        try:
            result = agent.analyze(
                symbol=symbol,
                market=market,
                period=period,
                use_ai=use_ai,
                force_refresh=force_refresh,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as exc:
            if market in ("a_stock", "us_stock"):
                return _stock_fundamental_fallback(symbol, market, period, exc, use_ai, username=username)
            raise
        analysis_path = visualizer.plot_analysis(result["df"], result["symbol"], save=True)
        if analysis_path:
            src = Path(analysis_path)
            if src.exists():
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                safe_symbol = result["symbol"].replace("-", "_")
                safe_user = _safe_username(username)
                unique_path = REPORTS_DIR / f"{safe_user}_{safe_symbol}_{result['market']}_{period}_{stamp}_analysis.png"
                shutil.copy2(src, unique_path)
                analysis_path = str(unique_path)
        if result.get("backtest"):
            equity_curve = result["backtest"].equity_curve.dropna()
            equity_points = [
                {"date": idx.strftime("%Y-%m-%d"), "value": round(float(value), 2)}
                for idx, value in equity_curve.items()
            ]
            _validate_curve_points(
                equity_points,
                agent.config["backtest"]["initial_cash"],
                result["backtest"].total_return,
                "strategy",
            )
        if result.get("benchmark"):
            benchmark_curve = result["benchmark"].equity_curve.dropna()
            benchmark_points = [
                {"date": idx.strftime("%Y-%m-%d"), "value": round(float(value), 2)}
                for idx, value in benchmark_curve.items()
            ]
            _validate_curve_points(
                benchmark_points,
                agent.config["backtest"]["initial_cash"],
                result["benchmark"].total_return,
                "benchmark",
            )
        history_points = [
            {
                "date": idx.strftime("%Y-%m-%d"),
                "close": _json_number(row.get("close")),
                "ma20": _json_number(row.get("MA20")),
                "ma60": _json_number(row.get("MA60")),
                "rsi": _json_number(row.get("RSI"), 2),
            }
            for idx, row in result["df"].iterrows()
        ]

    latest_price = result["df"]["close"].iloc[-1] if not result["df"].empty else ""
    data_start = result["df"].index.min().strftime("%Y-%m-%d") if not result["df"].empty else "-"
    data_end = result["df"].index.max().strftime("%Y-%m-%d") if not result["df"].empty else "-"
    unit_label = _display_unit_label(result["market"], result["symbol"], data_end)
    valuation = result.get("valuation") or {}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = _build_search_summary(result, result["df"])
    analysis_result = {
        "symbol": result["symbol"],
        "market": result["market"],
        "market_label": MARKET_LABELS.get(result["market"], result["market"]),
        "display_name": _display_security_name(result["symbol"], result["market"], valuation),
        "unit_label": unit_label,
        "period": period,
        "latest_price": f"{latest_price:.4f}" if latest_price != "" else "",
        "data_range": f"{data_start} 至 {data_end}",
        "data_points": len(result["df"]),
        "generated_at": now,
        "log": buffer.getvalue(),
        "analysis_image": _to_image_url(analysis_path),
        "equity_image": None,
        "equity_points": equity_points,
        "benchmark_points": benchmark_points,
        "history_points": history_points,
        "valuation": valuation,
        "watchlist_item": _watchlist_valuation_payload(result["symbol"], result["market"], valuation, summary),
        "summary": summary,
    }
    _write_history_item({
        "time": now[:16],
        "symbol": analysis_result["symbol"],
        "market": analysis_result["market"],
        "period": analysis_result["period"],
        "use_ai": bool(use_ai),
        "latest_price": analysis_result["latest_price"] or "-",
        "data_range": analysis_result["data_range"],
        "data_points": analysis_result["data_points"],
        "analysis_image": analysis_result["analysis_image"],
    }, username=username)
    return analysis_result


def _parse_natural_language_command(text: str) -> dict:
    raw = (text or "").strip()
    lowered = raw.lower()
    if any(key in raw for key in ("分析", "看看", "诊断", "研究", "analyze", "report")):
        market = ""
        if any(key in lowered for key in ("btc", "eth", "crypto", "比特币", "以太坊")):
            market = "crypto"
        elif any(key in lowered for key in ("us", "nvda", "aapl", "tsla", "美股")):
            market = "us_stock"
        elif "基金" in raw:
            market = "fund"
        elif "a股" in raw or "股票" in raw:
            market = "a_stock"

        period = "max"
        for candidate in ("1mo", "3mo", "6mo", "1y", "2y", "3y", "5y", "10y", "20y", "50y", "max"):
            if candidate in lowered:
                period = candidate
                break

        symbol = ""
        code_match = re.search(r"\b[A-Z]{2,10}(?:-[A-Z]{2,10})?\b", raw.upper())
        if code_match:
            symbol = code_match.group(0)
        digit_match = re.search(r"\b\d{6}\b", raw)
        if digit_match:
            symbol = digit_match.group(0)
        if symbol:
            return {
                "intent": "analyze",
                "symbol": symbol,
                "market": market or "auto",
                "period": period,
                "use_ai": "ai" in lowered or "报告" in raw,
            }
    return {"intent": "unknown", "reply": "没有识别到请求。可以输入：分析 002982 基金，或 analyze NVDA 1mo。"}


def _handle_prompt(prompt: str) -> tuple[dict | None, str | None, str | None, dict]:
    parsed = _parse_natural_language_command(prompt)
    wants_ai = any(k in prompt.lower() for k in ("ai", "llm", "report"))
    form = _default_form()
    form.update({"prompt": prompt, "use_ai": wants_ai})
    if parsed.get("intent") == "analyze":
        market = _normalize_market(parsed.get("market") or "auto")
        symbol, market = _resolve_search_symbol(parsed.get("symbol") or "", market)
        period = _normalize_period(parsed.get("period") or "max")
        use_ai = bool(parsed.get("use_ai", False) and wants_ai)
        form.update({"symbol": symbol, "market": market, "period": period, "use_ai": use_ai})
        return _run_analysis(symbol, market, period, use_ai), None, None, form
    return None, parsed.get("reply") or "没有识别到请求。", None, form


def _reader_payload(version: str) -> dict:
    presets = {
        "个人投资者版": {
            "note": "当前：个人投资者版",
            "conclusion": "关注回撤、数据完整性和持仓集中度。",
        },
        "小资金账户版": {
            "note": "当前：小资金账户版",
            "conclusion": "关注仓位、承受亏损和交易成本。",
        },
        "业余量化版": {
            "note": "当前：业余量化版",
            "conclusion": "关注收益、回撤、波动和样本区间。",
        },
        "小型投研团队版": {
            "note": "当前：小型投研团队版",
            "conclusion": "关注数据来源、风险边界和复盘记录。",
        },
    }
    return presets.get(version) or presets["个人投资者版"]


def _render_analysis(result=None, note=None, error=None, form=None):
    broker_ready = _broker_data_ready()
    return render_template_string(
        PAGE_TEMPLATE,
        result=result,
        note=note,
        error=error,
        form=form or _default_form(),
        default_symbol=agent.config["market"]["default_symbol"],
        broker_data_ready=broker_ready,
        broker_data_source_label=_broker_data_source_label() if broker_ready else "公开行情",
    )


@app.route("/analysis", methods=["GET", "POST"])
def analysis_page():
    result = None
    note = None
    error = None
    form = _default_form()
    if request.method == "POST":
        mode = request.form.get("mode", "")
        try:
            if mode == "analyze":
                market = _normalize_market(request.form.get("market", "fund"))
                symbol, market = _resolve_search_symbol(request.form.get("symbol", ""), market)
                period = _normalize_period(request.form.get("period", "max"))
                start_date = _normalize_backtest_date(request.form.get("start_date"), "开始日期")
                end_date = _normalize_backtest_date(request.form.get("end_date"), "结束日期")
                if start_date and end_date and start_date > end_date:
                    raise ValueError("开始日期不能晚于结束日期。")
                use_ai = request.form.get("use_ai", "false") == "true"
                reader_version = (request.form.get("reader_version") or "个人投资者版").strip() or "个人投资者版"
                analysis_period = "max" if (start_date or end_date) else period
                form.update({
                    "symbol": symbol,
                    "market": market,
                    "period": period,
                    "start_date": start_date,
                    "end_date": end_date,
                    "use_ai": use_ai,
                    "reader_version": reader_version,
                })
                if not symbol:
                    error = "请输入标的代码。"
                else:
                    result = _run_analysis(
                        symbol,
                        market,
                        analysis_period,
                        use_ai,
                        start_date=start_date or None,
                        end_date=end_date or None,
                    )
            elif mode == "chat":
                prompt = (request.form.get("prompt", "") or "").strip()
                if not prompt:
                    error = "请输入请求内容。"
                else:
                    result, note, error, form = _handle_prompt(prompt)
            else:
                error = "Unknown request type."
        except ValueError as exc:
            error = str(exc)
        except Exception as exc:
            traceback.print_exc()
            app.logger.exception("analysis request failed")
            error = _friendly_error(exc)
    return _render_analysis(result=result, note=note, error=error, form=form)


@app.route("/")
def index():
    return redirect(url_for("analysis_page"))


@app.route("/reports/<path:filename>")
def serve_report(filename: str):
    path = (REPORTS_DIR / filename).resolve()
    if REPORTS_DIR.resolve() not in path.parents or not path.exists():
        return "Not found", 404
    return send_from_directory(REPORTS_DIR, filename)


@app.route("/health")
def health():
    return {"status": "ok", "page": "analysis"}


@app.route("/api/broker/status")
def broker_status_api():
    status = broker_adapter.status()
    return jsonify({
        "ok": True,
        "enabled": status.enabled,
        "connected": status.connected,
        "provider": status.provider,
        "message": status.message,
    })


@app.route("/api/watchlist/realtime", methods=["POST"])
def watchlist_realtime_api():
    payload = request.get_json(silent=True)
    raw_items = payload.get("items") if isinstance(payload, dict) else []
    if not isinstance(raw_items, list):
        raw_items = []
    refreshed = []
    errors = []
    for raw_item in raw_items[:30]:
        if not isinstance(raw_item, dict):
            continue
        raw_symbol = str(raw_item.get("symbol") or "").strip()
        raw_market = str(raw_item.get("market") or "auto").strip() or "auto"
        if not raw_symbol:
            continue
        try:
            symbol, market = _resolve_search_symbol(raw_symbol, _normalize_market(raw_market))
            df = agent.data_fetcher.fetch(symbol, market=market, period="1y", force_refresh=True)
            df = add_all_indicators(df, config=agent.config.get("strategy"))
            signals = generate_signal_summary(df)
            summary = _build_search_summary({"symbol": symbol, "market": market, "signals": signals}, df)
            valuation = fetch_stock_value(symbol, market) if market in ("us_stock", "a_stock", "fund") else None
            item = _watchlist_valuation_payload(symbol, market, valuation, summary)
            item["name"] = _display_security_name(symbol, market, valuation)
            item["refreshedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            item["dataSource"] = "remote"
            refreshed.append(item)
        except Exception as exc:
            errors.append({"symbol": raw_symbol, "error": _friendly_error(exc)})
            fallback = dict(raw_item)
            fallback["symbol"] = raw_symbol
            fallback["conclusion"] = "实时获取失败"
            fallback["status"] = "status-high"
            fallback["valuationSource"] = "remote-error"
            fallback["metricMode"] = fallback.get("metricMode") or "market"
            fallback["error"] = _friendly_error(exc)
            refreshed.append(fallback)
    return jsonify({
        "ok": True,
        "items": refreshed,
        "errors": errors,
        "refreshed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


@app.route("/api/ui/report_config", methods=["POST"])
def save_report_config_api():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}
    config = {
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "page": str(payload.get("page") or "/analysis")[:500],
        "title": str(payload.get("title") or "策略研究报告")[:120],
        "reader_version": str(payload.get("reader_version") or "个人投资者版")[:80],
        "toggles": payload.get("toggles") if isinstance(payload.get("toggles"), dict) else {},
        "form": payload.get("form") if isinstance(payload.get("form"), dict) else {},
    }
    state = _read_json_file(_user_file(_current_user(), "ui_state.json"), {})
    state["report_config"] = config
    _write_json_file(_user_file(_current_user(), "ui_state.json"), state)
    return jsonify({"ok": True, "message": "已保存", "config": config})


@app.route("/api/ui/share_link", methods=["POST"])
def share_report_link_api():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}
    token = uuid4().hex[:16]
    share_dir = DATA_DIR / "shared_reports"
    snapshot = {
        "token": token,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "title": str(payload.get("title") or "策略研究报告"),
        "page": "/analysis",
        "report_config": payload,
    }
    _write_json_file(share_dir / f"{token}.json", snapshot)
    return jsonify({"ok": True, "share_url": url_for("analysis_page", _external=True), "snapshot": snapshot})


@app.route("/api/ui/reader_version", methods=["POST"])
def reader_version_api():
    payload = request.get_json(silent=True)
    version = str((payload or {}).get("version") or "个人投资者版")
    data = _reader_payload(version)
    return jsonify({"ok": True, "version": version, **data})


@app.route("/api/ui/explain")
def explain_metric_api():
    name = (request.args.get("name") or "").strip()
    explanations = {
        "年化收益": "把区间收益换算为一年维度后的收益率，用于比较不同周期表现。",
        "超额收益": "策略收益减去基准收益后的差额，用来观察是否跑赢基准。",
        "夏普比率": "单位波动带来的收益质量参考，数值越高通常表示风险调整后表现越好。",
        "最大回撤": "从历史高点跌到后续低点的最大跌幅，用于衡量最差持有体验。",
        "胜率": "盈利周期占全部统计周期的比例，不能单独代表策略好坏。",
        "跟踪误差": "策略相对基准收益差的波动程度，越高说明偏离基准越明显。",
    }
    explanation = explanations.get(name) or f"{name} 是当前分析页中的报告字段，用于辅助理解收益、风险、因子有效性或报告口径。"
    return jsonify({"ok": True, "name": name, "explanation": explanation})


@app.route("/api/report_followup", methods=["POST"])
def report_followup_api():
    question = (request.form.get("question") or "").strip()
    context = (request.form.get("context") or "").strip()
    if not question:
        return jsonify({"ok": False, "error": "请输入追问内容。"}), 400
    if agent.llm:
        try:
            answer = agent.llm.chat(
                "你是投资复盘与风险分析报告助手。保持观察、复核、风险提示口径，不给下单指令。",
                f"报告上下文：\n{context[:3000]}\n\n用户问题：{question}",
            ).strip()
        except Exception:
            answer = ""
        if answer:
            return jsonify({"ok": True, "answer": answer, "history": []})
    fallback = "可以继续追问。当前最值得复核的是：数据是否完整、回撤是否扩大、持仓是否集中、交易成本是否影响收益。"
    return jsonify({"ok": True, "answer": fallback, "history": []})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    host = os.getenv("HOST", "127.0.0.1")
    if sys.stdout:
        print(f"Analysis page started: http://{host}:{port}/analysis")
    app.run(host=host, port=port, debug=False)
