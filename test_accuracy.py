#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lightweight data/chart accuracy checks for the web app."""

from core.data_fetcher import DataFetcher
from core.indicators import add_all_indicators
from core.backtest import BacktestEngine


def check_ohlcv(symbol: str = "002982", market: str = "fund", period: str = "1mo") -> None:
    fetcher = DataFetcher()
    df = fetcher.fetch(symbol, market=market, period=period)
    expected = ["open", "high", "low", "close", "volume"]
    assert list(df.columns) == expected, f"Unexpected columns: {df.columns.tolist()}"
    assert df.index.is_monotonic_increasing, "Dates must be sorted ascending"
    assert not df.index.duplicated().any(), "Dates must be unique"
    assert not df[["open", "high", "low", "close"]].isna().any().any(), "OHLC contains NaN"
    assert (df["close"] > 0).all(), "Close prices must be positive"
    assert (df["high"] >= df[["open", "close"]].max(axis=1)).all(), "High below open/close"
    assert (df["low"] <= df[["open", "close"]].min(axis=1)).all(), "Low above open/close"


def check_backtest_curve(symbol: str = "002982", market: str = "fund", period: str = "1mo") -> None:
    fetcher = DataFetcher()
    df = add_all_indicators(fetcher.fetch(symbol, market=market, period=period))
    df["signal"] = 1
    engine = BacktestEngine(initial_cash=100000, fund_mode=(market == "fund"))
    result = engine.run(df, signal_col="signal")
    curve = result.equity_curve.dropna()
    assert len(curve) == len(df), "Equity curve length must match input data"
    assert abs(curve.iloc[0] - engine.initial_cash) < 1e-6, "Curve must start at initial cash"
    expected_last = engine.initial_cash * (1 + result.total_return)
    assert abs(curve.iloc[-1] - expected_last) < 1e-6, "Curve last value mismatches return"


if __name__ == "__main__":
    check_ohlcv()
    check_backtest_curve()
    print("accuracy checks passed")
