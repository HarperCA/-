# -*- coding: utf-8 -*-
from __future__ import annotations

import pandas as pd


def _latest_value(row: pd.Series, *names: str, default: float = 0.0) -> float:
    for name in names:
        if name in row and pd.notna(row[name]):
            try:
                return float(row[name])
            except Exception:
                continue
    return default


def generate_composite_signal(df: pd.DataFrame) -> tuple[int, dict]:
    """
    Generate a conservative observation signal from common technical columns.

    Return values:
    - 1: stronger observation state
    - 0: neutral / insufficient evidence
    - -1: weaker observation state

    This module intentionally avoids direct trade instructions. It is used by
    the agent to frame review signals and risk checks.
    """
    if df is None or df.empty:
        return 0, {"状态": "数据为空", "说明": "无法生成观察信号"}

    latest = df.iloc[-1]
    score = 0
    details: dict[str, str] = {}

    close = _latest_value(latest, "close", "Close", "收盘")
    ma_short = _latest_value(latest, "MA5", "MA10", "ma5", "ma10")
    ma_long = _latest_value(latest, "MA20", "MA30", "MA60", "ma20", "ma30", "ma60")
    if close and ma_short and ma_long:
        if ma_short > ma_long and close >= ma_short:
            score += 1
            details["均线"] = "偏强：短期均线在长期均线上方"
        elif ma_short < ma_long and close <= ma_short:
            score -= 1
            details["均线"] = "偏弱：短期均线在长期均线下方"
        else:
            details["均线"] = "中性：价格和均线关系不清晰"

    rsi = _latest_value(latest, "RSI", "rsi", default=float("nan"))
    if pd.notna(rsi):
        if rsi >= 70:
            score -= 1
            details["RSI"] = "过热：需要警惕短期波动"
        elif rsi <= 30:
            score += 1
            details["RSI"] = "偏低：进入观察区，但仍需复核趋势"
        else:
            details["RSI"] = "中性：未出现明显过热或过冷"

    macd = _latest_value(latest, "MACD", "macd", default=float("nan"))
    signal = _latest_value(latest, "MACD_signal", "MACD_SIGNAL", "macd_signal", default=float("nan"))
    if pd.notna(macd) and pd.notna(signal):
        if macd > signal:
            score += 1
            details["MACD"] = "偏强：MACD 位于信号线上方"
        elif macd < signal:
            score -= 1
            details["MACD"] = "偏弱：MACD 位于信号线下方"

    if score >= 2:
        composite = 1
        state = "偏强观察"
    elif score <= -2:
        composite = -1
        state = "偏弱观察"
    else:
        composite = 0
        state = "中性观察"

    details["综合状态"] = state
    details["综合分"] = str(score)
    return composite, details


def signal_to_action(signal: int, current_position: int = 0) -> str:
    """Translate signal into cautious review wording, not a trade command."""
    if signal > 0:
        return "偏强观察，进入复核清单"
    if signal < 0:
        return "偏弱观察，优先复核风险"
    return "中性观察，继续跟踪"
