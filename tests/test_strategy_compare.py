import unittest

import pandas as pd

from core.strategy_compare import _rsi_signal, compare_strategies


class StrategyCompareTest(unittest.TestCase):
    def test_rsi_signal_exits_after_overbought_reading(self):
        dates = pd.date_range("2025-01-01", periods=5, freq="D")
        df = pd.DataFrame({"RSI": [50, 25, 40, 75, 45]}, index=dates)

        signal = _rsi_signal(df)

        self.assertEqual(signal.tolist(), [0, 1, 1, 0, 0])

    def test_compare_returns_all_builtin_strategies(self):
        dates = pd.date_range("2025-01-01", periods=180, freq="D")
        close = pd.Series(range(100, 280), index=dates, dtype=float)
        df = pd.DataFrame(
            {
                "open": close,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "volume": 1000,
            },
            index=dates,
        )

        rows = compare_strategies(df, initial_cash=100000, fund_mode=False)
        keys = {row["key"] for row in rows}

        self.assertEqual(
            keys,
            {
                "buy_hold",
                "ma",
                "rsi",
                "macd",
                "vmom",
                "composite",
                "robust_adaptive",
                "small_capital",
                "long_term_compounder",
                "market_adaptive",
            },
        )
        self.assertTrue(all("total_return" in row for row in rows))
        self.assertGreaterEqual(rows[0]["total_return"], rows[-1]["total_return"])

    def test_vol_adjusted_momentum_factor_is_available(self):
        dates = pd.date_range("2025-01-01", periods=220, freq="D")
        close = pd.Series(range(100, 320), index=dates, dtype=float)
        df = pd.DataFrame(
            {
                "open": close,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "volume": 1000,
            },
            index=dates,
        )

        rows = compare_strategies(df, initial_cash=100000, fund_mode=False)
        vmom = next(row for row in rows if row["key"] == "vmom")

        self.assertEqual(vmom["name"], "Vol-adjusted momentum factor")
        self.assertGreaterEqual(vmom["trade_count"], 1)

    def test_robust_adaptive_is_defensive_in_downtrend(self):
        dates = pd.date_range("2025-01-01", periods=180, freq="D")
        close = pd.Series(range(280, 100, -1), index=dates, dtype=float)
        df = pd.DataFrame(
            {
                "open": close,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "volume": 1000,
            },
            index=dates,
        )

        rows = compare_strategies(df, initial_cash=100000, fund_mode=False)
        robust = next(row for row in rows if row["key"] == "robust_adaptive")
        buy_hold = next(row for row in rows if row["key"] == "buy_hold")

        self.assertGreater(robust["total_return"], buy_hold["total_return"])
        self.assertLessEqual(abs(robust["max_drawdown"]), abs(buy_hold["max_drawdown"]))

    def test_small_capital_strategy_keeps_turnover_low(self):
        dates = pd.date_range("2025-01-01", periods=220, freq="D")
        up = list(range(100, 170))
        chop = [170 + (-1) ** i * 3 for i in range(80)]
        resume = list(range(170, 240))
        close = pd.Series(up + chop + resume, index=dates, dtype=float)
        df = pd.DataFrame(
            {
                "open": close,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "volume": 1000,
            },
            index=dates,
        )

        rows = compare_strategies(df, initial_cash=20000, fund_mode=False)
        small = next(row for row in rows if row["key"] == "small_capital")
        composite = next(row for row in rows if row["key"] == "composite")

        self.assertLess(small["trade_count"], composite["trade_count"])
        self.assertLessEqual(small["trade_count"], 6)

    def test_long_term_compounder_prefers_persistent_trends(self):
        dates = pd.date_range("2025-01-01", periods=320, freq="D")
        early = list(range(100, 180))
        pullback = list(range(180, 150, -1))
        long_trend = list(range(150, 360))
        close = pd.Series(early + pullback + long_trend, index=dates, dtype=float)
        df = pd.DataFrame(
            {
                "open": close,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "volume": 1000,
            },
            index=dates,
        )

        rows = compare_strategies(df, initial_cash=20000, fund_mode=False)
        long_term = next(row for row in rows if row["key"] == "long_term_compounder")

        self.assertGreater(long_term["total_return"], 0)
        self.assertLessEqual(long_term["trade_count"], 4)

    def test_market_adaptive_reduces_risk_in_bear_market(self):
        dates = pd.date_range("2025-01-01", periods=240, freq="D")
        early = list(range(200, 230))
        selloff = list(range(230, 80, -1))
        base = [80 + (i % 5) for i in range(60)]
        close = pd.Series(early + selloff + base, index=dates, dtype=float)
        df = pd.DataFrame(
            {
                "open": close,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "volume": 1000,
            },
            index=dates,
        )

        rows = compare_strategies(df, initial_cash=20000, fund_mode=False)
        adaptive = next(row for row in rows if row["key"] == "market_adaptive")
        buy_hold = next(row for row in rows if row["key"] == "buy_hold")

        self.assertGreater(adaptive["total_return"], buy_hold["total_return"])
        self.assertLess(abs(adaptive["max_drawdown"]), abs(buy_hold["max_drawdown"]))

    def test_market_adaptive_is_more_sensitive_to_fast_risk_spikes(self):
        dates = pd.date_range("2025-01-01", periods=220, freq="D")
        trend = list(range(100, 180))
        shock = [180, 176, 170, 162, 154, 148, 145, 142, 140, 139]
        rebound = list(range(140, 270))
        close = pd.Series(trend + shock + rebound, index=dates, dtype=float)
        df = pd.DataFrame(
            {
                "open": close,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "volume": 1000,
            },
            index=dates,
        )

        rows = compare_strategies(df, initial_cash=20000, fund_mode=False)
        adaptive = next(row for row in rows if row["key"] == "market_adaptive")
        small = next(row for row in rows if row["key"] == "small_capital")

        self.assertLessEqual(abs(adaptive["max_drawdown"]), abs(small["max_drawdown"]))


if __name__ == "__main__":
    unittest.main()
