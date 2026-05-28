# -*- coding: utf-8 -*-
from __future__ import annotations

import re


def safe_float(value, default: float = 0.0, minimum: float | None = None, maximum: float | None = None) -> float:
    try:
        parsed = float(str(value or "").strip())
    except (TypeError, ValueError):
        parsed = default
    if minimum is not None:
        parsed = max(parsed, minimum)
    if maximum is not None:
        parsed = min(parsed, maximum)
    return parsed


def normalize_market(value: str | None) -> str:
    market = (value or "fund").strip()
    return market if market in {"fund", "a_stock", "us_stock", "crypto"} else "fund"


def normalize_period(value: str | None) -> str:
    period = (value or "max").strip()
    allowed = {"1mo", "3mo", "6mo", "1y", "2y", "3y", "5y", "10y", "20y", "50y", "max"}
    return period if period in allowed else "max"


def normalize_symbol(symbol: str, market: str) -> str:
    symbol = (symbol or "").strip()
    if market in ("fund", "a_stock") and symbol.isdigit():
        return symbol.zfill(6)
    return symbol.upper() if market in ("us_stock", "crypto") else symbol


def safe_export_stem(stem: str) -> str:
    return re.sub(r"[^0-9A-Za-z_\-]+", "_", stem).strip("_") or "export"
