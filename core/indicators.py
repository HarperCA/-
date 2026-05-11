"""
技术指标计算模块
包含常用技术指标：MA、MACD、RSI、布林带、KDJ等
"""
import pandas as pd
import numpy as np


def add_moving_averages(df: pd.DataFrame, windows=(5, 10, 20, 30, 60)) -> pd.DataFrame:
    """计算多条移动平均线"""
    for w in windows:
        df[f"MA{w}"] = df["close"].rolling(window=w).mean()
    return df


def add_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """计算 MACD 指标"""
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    df["MACD"] = ema_fast - ema_slow
    df["MACD_Signal"] = df["MACD"].ewm(span=signal, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]
    return df


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """计算 RSI 相对强弱指标"""
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df


def add_bollinger(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    """计算布林带"""
    sma = df["close"].rolling(window=period).mean()
    std = df["close"].rolling(window=period).std()
    df["BB_Upper"] = sma + std_dev * std
    df["BB_Lower"] = sma - std_dev * std
    df["BB_Middle"] = sma
    return df


def add_kdj(df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
    """计算 KDJ 随机指标"""
    low_list = df["low"].rolling(window=n, min_periods=n).min()
    high_list = df["high"].rolling(window=n, min_periods=n).max()
    rsv = (df["close"] - low_list) / (high_list - low_list) * 100
    df["K"] = rsv.ewm(alpha=1 / m1, adjust=False).mean()
    df["D"] = df["K"].ewm(alpha=1 / m2, adjust=False).mean()
    df["J"] = 3 * df["K"] - 2 * df["D"]
    return df


def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """计算 ATR 真实波动幅度"""
    high_low = df["high"] - df["low"]
    high_close = np.abs(df["high"] - df["close"].shift())
    low_close = np.abs(df["low"] - df["close"].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(window=period).mean()
    return df


def add_volatility_adjusted_momentum(
    df: pd.DataFrame,
    momentum_window: int = 63,
    volatility_window: int = 20,
    zscore_window: int = 120,
) -> pd.DataFrame:
    """Add a volatility-adjusted momentum factor for research and backtests."""
    close = df["close"].astype(float)
    returns = close.pct_change()
    momentum = close.pct_change(momentum_window)
    volatility = returns.rolling(volatility_window, min_periods=volatility_window).std() * np.sqrt(252)

    factor = momentum / volatility.replace(0, np.nan)
    min_periods = max(20, zscore_window // 3)
    factor_mean = factor.rolling(zscore_window, min_periods=min_periods).mean()
    factor_std = factor.rolling(zscore_window, min_periods=min_periods).std()

    df["Factor_VMOM"] = factor
    df["Factor_VMOM_Z"] = (factor - factor_mean) / factor_std.replace(0, np.nan)
    return df


def add_all_indicators(df: pd.DataFrame, config: dict = None) -> pd.DataFrame:
    """一键添加所有技术指标"""
    df = df.copy()
    df = add_moving_averages(df)
    df = add_macd(df)
    df = add_rsi(df, period=config.get("rsi_period", 14) if config else 14)
    df = add_bollinger(df)
    df = add_kdj(df)
    df = add_atr(df)
    factor_config = (config or {}).get("factors", {}) if isinstance(config, dict) else {}
    df = add_volatility_adjusted_momentum(
        df,
        momentum_window=factor_config.get("vmom_momentum_window", 63),
        volatility_window=factor_config.get("vmom_volatility_window", 20),
        zscore_window=factor_config.get("vmom_zscore_window", 120),
    )
    return df


def generate_signal_summary(df: pd.DataFrame) -> dict:
    """基于最新数据，生成各指标的信号摘要"""
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    signals = {}

    # MA 多头排列判断
    ma_short = latest.get("MA10", np.nan)
    ma_long = latest.get("MA30", np.nan)
    if not pd.isna(ma_short) and not pd.isna(ma_long):
        signals["均线"] = "多头" if ma_short > ma_long else "空头"

    # MACD
    macd = latest.get("MACD", np.nan)
    macd_sig = latest.get("MACD_Signal", np.nan)
    if not pd.isna(macd) and not pd.isna(macd_sig):
        signals["MACD"] = "金叉/多头" if macd > macd_sig else "死叉/空头"

    # RSI
    rsi = latest.get("RSI", np.nan)
    if not pd.isna(rsi):
        if rsi > 70:
            signals["RSI"] = f"超买({rsi:.1f})"
        elif rsi < 30:
            signals["RSI"] = f"超卖({rsi:.1f})"
        else:
            signals["RSI"] = f"中性({rsi:.1f})"

    # 布林带
    close = latest["close"]
    bb_upper = latest.get("BB_Upper", np.nan)
    bb_lower = latest.get("BB_Lower", np.nan)
    if not pd.isna(bb_upper) and not pd.isna(bb_lower):
        if close > bb_upper:
            signals["布林带"] = "突破上轨"
        elif close < bb_lower:
            signals["布林带"] = "跌破下轨"
        else:
            signals["布林带"] = "轨道内"

    # KDJ
    j = latest.get("J", np.nan)
    if not pd.isna(j):
        signals["KDJ"] = "超买区" if j > 80 else ("超卖区" if j < 20 else "中性")

    vmom = latest.get("Factor_VMOM", np.nan)
    vmom_z = latest.get("Factor_VMOM_Z", np.nan)
    if not pd.isna(vmom):
        if vmom > 0.35:
            label = "强正动量"
        elif vmom > 0:
            label = "正动量"
        elif vmom < -0.35:
            label = "强负动量"
        else:
            label = "负动量"
        suffix = f"，Z={vmom_z:.2f}" if not pd.isna(vmom_z) else ""
        signals["波动率调整动量"] = f"{label}({vmom:.2f}{suffix})"

    return signals
