import unittest

import pandas as pd

from core.factor_research import (
    VmomParams,
    build_vmom_panel,
    cross_sectional_ic,
    run_vmom_parameter_grid,
)


def _make_asset(start: float, daily_return: float, periods: int = 180) -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", periods=periods, freq="D")
    close = pd.Series(
        [start * ((1 + daily_return) ** i) for i in range(periods)],
        index=dates,
        dtype=float,
    )
    return pd.DataFrame(
        {
            "open": close,
            "high": close * 1.002,
            "low": close * 0.998,
            "close": close,
            "volume": 1000,
        },
        index=dates,
    )


class FactorResearchTest(unittest.TestCase):
    def test_vmom_cross_sectional_ic_is_positive_for_persistent_trends(self):
        series_by_asset = {
            "fast_up": _make_asset(100, 0.0030),
            "slow_up": _make_asset(100, 0.0012),
            "flat": _make_asset(100, 0.0001),
            "down": _make_asset(100, -0.0010),
        }

        panel = build_vmom_panel(
            series_by_asset,
            params=VmomParams(momentum_window=42, volatility_window=10, zscore_window=80),
            forward_days=(5,),
        )
        ic = cross_sectional_ic(panel, forward_col="forward_return_5d", min_assets=4)

        self.assertFalse(ic.empty)
        self.assertGreater(ic["spearman_ic"].mean(), 0)

    def test_parameter_grid_returns_ranked_rows(self):
        series_by_asset = {
            "fast_up": _make_asset(100, 0.0030),
            "slow_up": _make_asset(100, 0.0012),
            "flat": _make_asset(100, 0.0001),
            "down": _make_asset(100, -0.0010),
        }

        grid = run_vmom_parameter_grid(
            series_by_asset,
            momentum_windows=(21, 42),
            volatility_windows=(10, 20),
            zscore_window=80,
            horizon=5,
            min_assets=4,
        )

        self.assertEqual(len(grid), 4)
        self.assertIn("spearman_ic_mean", grid.columns)
        self.assertGreaterEqual(grid.iloc[0]["spearman_ic_mean"], grid.iloc[-1]["spearman_ic_mean"])


if __name__ == "__main__":
    unittest.main()
