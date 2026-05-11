"""Multiple strategy backtest comparison helpers."""

from __future__ import annotations

import pandas as pd
import numpy as np

from core.backtest import BacktestEngine
from core.indicators import add_all_indicators


def _ma_signal(df: pd.DataFrame) -> pd.Series:
    return (df["MA10"] > df["MA30"]).astype(int)


def _rsi_signal(df: pd.DataFrame) -> pd.Series:
    signal = pd.Series(pd.NA, index=df.index, dtype="object")
    signal[df["RSI"] < 35] = 1
    signal[df["RSI"] > 70] = 0
    return signal.ffill().fillna(0).astype(int)


def _macd_signal(df: pd.DataFrame) -> pd.Series:
    return (df["MACD"] > df["MACD_Signal"]).astype(int)


def _vmom_signal(df: pd.DataFrame) -> pd.Series:
    """Volatility-adjusted momentum factor timing signal."""
    factor = df["Factor_VMOM"]
    zscore = df["Factor_VMOM_Z"]

    entry = (factor > 0.20) & (zscore.fillna(0) > -0.50)
    exit_ = (factor < 0) | (zscore < -1.00)

    position = pd.Series(pd.NA, index=df.index, dtype="object")
    position[entry] = 1
    position[exit_] = 0
    return position.ffill().fillna(0).astype(int)


def _composite_signal(df: pd.DataFrame) -> pd.Series:
    score = pd.Series(0, index=df.index)
    score += (df["MA10"] > df["MA30"]).astype(int)
    score += (df["MACD"] > df["MACD_Signal"]).astype(int)
    score += (df["RSI"] < 65).astype(int)
    return (score >= 2).astype(int)


def _robust_adaptive_signal(df: pd.DataFrame) -> pd.Series:
    """
    Defensive trend strategy for single-asset long/cash backtests.

    The strategy is deliberately simple and hard to overfit:
    - only buy when medium/long trend and multi-horizon momentum agree
    - avoid assets in deep drawdown or abnormal realized volatility
    - allow pullback entries inside a confirmed uptrend
    """
    close = df["close"].astype(float)
    high = df.get("high", close).astype(float)
    low = df.get("low", close).astype(float)

    ma20 = close.rolling(20, min_periods=20).mean()
    ma60 = close.rolling(60, min_periods=60).mean()
    ma120 = close.rolling(120, min_periods=120).mean()

    returns = close.pct_change().fillna(0)
    vol20 = returns.rolling(20, min_periods=20).std() * (252 ** 0.5)
    vol80 = returns.rolling(80, min_periods=40).std() * (252 ** 0.5)

    high_low = high - low
    high_close = (high - close.shift()).abs()
    low_close = (low - close.shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr20 = tr.rolling(20, min_periods=20).mean()
    atr_pct = atr20 / close

    peak120 = close.rolling(120, min_periods=60).max()
    drawdown120 = close / peak120 - 1

    mom21 = close.pct_change(21)
    mom63 = close.pct_change(63)
    mom126 = close.pct_change(126)

    trend_score = (
        (close > ma60).astype(int)
        + (ma20 > ma60).astype(int)
        + (ma60 > ma120).astype(int)
    )
    momentum_score = (
        (mom21 > 0).astype(int)
        + (mom63 > 0).astype(int)
        + (mom126 > 0).astype(int)
    )

    volatility_ok = (vol20 <= vol80 * 1.6) | vol80.isna()
    drawdown_ok = drawdown120 > -0.18
    liquidity_proxy_ok = atr_pct < 0.09

    confirmed_uptrend = (trend_score >= 2) & (momentum_score >= 2)
    pullback_in_uptrend = (trend_score >= 2) & (mom63 > 0) & (df["RSI"].between(35, 58))
    risk_ok = volatility_ok & drawdown_ok & liquidity_proxy_ok

    entry = (confirmed_uptrend | pullback_in_uptrend) & risk_ok
    exit_ = (trend_score <= 1) | (momentum_score == 0) | ~risk_ok

    position = pd.Series(pd.NA, index=df.index, dtype="object")
    position[entry] = 1
    position[exit_] = 0
    return position.ffill().fillna(0).astype(int)


def _apply_holding_rules(
    raw_position: pd.Series,
    min_hold_days: int = 15,
    cooldown_days: int = 10,
) -> pd.Series:
    """Reduce turnover by enforcing a minimum hold and post-exit cooldown."""
    target = raw_position.fillna(0).astype(int).clip(0, 1)
    position = []
    current = 0
    hold_days = 0
    cooldown = 0

    for desired in target:
        if current:
            hold_days += 1
            if desired == 0 and hold_days >= min_hold_days:
                current = 0
                hold_days = 0
                cooldown = cooldown_days
        else:
            if cooldown > 0:
                cooldown -= 1
            elif desired == 1:
                current = 1
                hold_days = 1
        position.append(current)

    return pd.Series(position, index=raw_position.index, dtype=int)


def _small_capital_signal(df: pd.DataFrame) -> pd.Series:
    """
    Low-turnover strategy selector for small accounts.

    Small accounts are more sensitive to commissions, slippage, and noisy
    overtrading, so this strategy rotates slowly between cash and a small set of
    simple signals using trailing risk-adjusted performance.
    """
    close = df["close"].astype(float)
    returns = close.pct_change().fillna(0)
    candidates = pd.DataFrame(
        {
            "cash": pd.Series(0, index=df.index),
            "buy_hold": pd.Series(1, index=df.index),
            "ma": _ma_signal(df),
            "macd": _macd_signal(df),
            "vmom": _vmom_signal(df),
            "robust": _robust_adaptive_signal(df),
        }
    ).fillna(0).astype(int)

    candidate_returns = candidates.shift(1).fillna(0).mul(returns, axis=0)
    lookback = 42
    rolling_return = (1 + candidate_returns).rolling(lookback, min_periods=21).apply(np.prod, raw=True) - 1
    rolling_vol = candidate_returns.rolling(lookback, min_periods=21).std() * (252 ** 0.5)
    score = (rolling_return - 0.65 * rolling_vol).fillna(-999.0)
    score["cash"] = 0.0

    selection_score = score.shift(1).fillna(-999.0)
    selection_score["cash"] = 0.0
    selected = selection_score.idxmax(axis=1)
    raw_position = pd.Series(
        [int(candidates.iloc[i][name]) for i, name in enumerate(selected)],
        index=df.index,
    )
    return _apply_holding_rules(raw_position, min_hold_days=15, cooldown_days=10)


def _long_term_compounder_signal(df: pd.DataFrame) -> pd.Series:
    """
    Long-term compounding selector for small accounts.

    It uses the same low-cost idea as small_capital, but changes position less
    often and gives each selected regime more time to work.
    """
    close = df["close"].astype(float)
    returns = close.pct_change().fillna(0)
    candidates = pd.DataFrame(
        {
            "cash": pd.Series(0, index=df.index),
            "buy_hold": pd.Series(1, index=df.index),
            "ma": _ma_signal(df),
            "macd": _macd_signal(df),
            "vmom": _vmom_signal(df),
            "robust": _robust_adaptive_signal(df),
            "small": _small_capital_signal(df),
        }
    ).fillna(0).astype(int)

    candidate_returns = candidates.shift(1).fillna(0).mul(returns, axis=0)
    lookback = 42
    rolling_return = (1 + candidate_returns).rolling(lookback, min_periods=21).apply(np.prod, raw=True) - 1
    rolling_vol = candidate_returns.rolling(lookback, min_periods=21).std() * (252 ** 0.5)
    rolling_loss = candidate_returns.rolling(lookback, min_periods=21).apply(
        lambda values: abs(min(0.0, values.sum())),
        raw=True,
    )

    score = (rolling_return - 0.60 * rolling_vol - 0.40 * rolling_loss).fillna(-999.0)
    score["cash"] = 0.0
    selection_score = score.shift(1).fillna(-999.0)
    selection_score["cash"] = 0.0
    selected = selection_score.idxmax(axis=1)
    raw_position = pd.Series(
        [int(candidates.iloc[i][name]) for i, name in enumerate(selected)],
        index=df.index,
    )
    return _apply_holding_rules(raw_position, min_hold_days=20, cooldown_days=15)


def _market_regime_series(df: pd.DataFrame) -> pd.Series:
    """Classify each bar into a simple, backward-looking market regime."""
    close = df["close"].astype(float)
    returns = close.pct_change().fillna(0)
    ma20 = close.rolling(20, min_periods=20).mean()
    ma60 = close.rolling(60, min_periods=40).mean()
    ma120 = close.rolling(120, min_periods=80).mean()
    mom20 = close.pct_change(20)
    mom60 = close.pct_change(60)
    vol20 = returns.rolling(20, min_periods=20).std() * (252 ** 0.5)
    vol60 = returns.rolling(60, min_periods=40).std() * (252 ** 0.5)
    peak60 = close.rolling(60, min_periods=30).max()
    drawdown60 = close / peak60 - 1

    regime = pd.Series("range", index=df.index, dtype="object")
    panic = (drawdown60 <= -0.08) | ((vol20 > vol60 * 1.50) & vol60.notna())
    bear = ((close < ma60) & (mom20 < -0.005)) | ((close < ma20) & (mom60 < 0))
    recovery = (close > ma20) & (mom20 > 0) & ((close <= ma60) | (mom60 < 0))
    bull = (close > ma60) & (ma20 > ma60) & ((ma60 > ma120 * 0.98) | ma120.isna()) & (mom60 > -0.02)

    regime[panic] = "panic"
    regime[bear & ~panic] = "bear"
    regime[recovery & ~(panic | bear)] = "recovery"
    regime[bull & ~(panic | bear)] = "bull"
    return regime


def _risk_off_series(df: pd.DataFrame) -> pd.Series:
    """Return True when recent risk is high enough to force cash."""
    close = df["close"].astype(float)
    returns = close.pct_change().fillna(0)
    vol10 = returns.rolling(10, min_periods=10).std() * (252 ** 0.5)
    vol40 = returns.rolling(40, min_periods=20).std() * (252 ** 0.5)
    peak20 = close.rolling(20, min_periods=10).max()
    drawdown20 = close / peak20 - 1
    mom10 = close.pct_change(10)
    mom20 = close.pct_change(20)

    return (
        (drawdown20 <= -0.055)
        | ((vol10 > vol40 * 1.35) & vol40.notna() & (mom10 < 0))
        | ((mom10 < -0.035) & (mom20 < 0))
    ).fillna(False)


def _market_adaptive_signal(df: pd.DataFrame) -> pd.Series:
    """
    Timely regime-aware strategy.

    The strategy changes behavior by market state:
    - panic/bear: cash
    - recovery: small-capital selector
    - bull: long-term compounder
    - range: small-capital selector
    """
    regime = _market_regime_series(df).shift(1).fillna("range")
    candidates = pd.DataFrame(
        {
            "cash": pd.Series(0, index=df.index),
            "small": _small_capital_signal(df),
            "long": _long_term_compounder_signal(df),
            "robust": _robust_adaptive_signal(df),
            "vmom": _vmom_signal(df),
        }
    ).fillna(0).astype(int)

    selected = pd.Series("small", index=df.index, dtype="object")
    selected[regime.isin(["panic", "bear"])] = "cash"
    selected[regime == "recovery"] = "small"
    selected[regime == "bull"] = "long"
    selected[regime == "range"] = "small"

    raw_position = pd.Series(
        [int(candidates.iloc[i][name]) for i, name in enumerate(selected)],
        index=df.index,
    )
    position = _apply_holding_rules(raw_position, min_hold_days=10, cooldown_days=5)
    risk_off = _risk_off_series(df).shift(1).fillna(False)
    position[risk_off] = 0
    return position.astype(int)


STRATEGIES = {
    "buy_hold": ("Buy and hold", lambda df: pd.Series(1, index=df.index)),
    "ma": ("MA10/MA30 trend", _ma_signal),
    "rsi": ("RSI reversal", _rsi_signal),
    "macd": ("MACD trend", _macd_signal),
    "vmom": ("Vol-adjusted momentum factor", _vmom_signal),
    "composite": ("Composite vote", _composite_signal),
    "robust_adaptive": ("Robust adaptive trend", _robust_adaptive_signal),
    "small_capital": ("Small capital low-turnover", _small_capital_signal),
    "long_term_compounder": ("Long-term compounder", _long_term_compounder_signal),
    "market_adaptive": ("Market adaptive regime switcher", _market_adaptive_signal),
}


def compare_strategies(
    df: pd.DataFrame,
    initial_cash: float = 100000,
    fund_mode: bool = False,
    config: dict | None = None,
) -> list[dict]:
    data = add_all_indicators(df.copy(), config=config)
    rows = []
    engine = BacktestEngine(initial_cash=initial_cash, fund_mode=fund_mode)
    for key, (name, signal_fn) in STRATEGIES.items():
        test_df = data.copy()
        test_df["strategy_signal"] = signal_fn(test_df).fillna(0).astype(int)
        result = engine.run(test_df, signal_col="strategy_signal")
        rows.append(
            {
                "key": key,
                "name": name,
                "total_return": result.total_return,
                "cagr": result.cagr,
                "max_drawdown": result.max_drawdown,
                "sharpe_ratio": result.sharpe_ratio,
                "trade_count": result.trade_count,
                "win_rate": result.win_rate,
                "final_value": float(result.equity_curve.iloc[-1]),
            }
        )
    return sorted(rows, key=lambda item: item["total_return"], reverse=True)
