import unittest

import pandas as pd

from core.random_strategy_search import (
    Condition,
    RandomStrategySpec,
    build_signal,
    prepare_market_data,
    run_random_strategy_search,
)


class RandomStrategySearchTest(unittest.TestCase):
    def _dataset(self):
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
        return {
            "label": "synthetic",
            "path": "synthetic.csv",
            "fund_mode": False,
            "data": prepare_market_data(df),
        }

    def test_build_signal_uses_conditions_and_holding_rules(self):
        dataset = self._dataset()
        spec = RandomStrategySpec(
            key="test",
            entry=(Condition("mom_20", ">", 0.01),),
            exit=(Condition("mom_20", "<", -0.01),),
            min_hold_days=5,
            cooldown_days=0,
        )

        signal = build_signal(dataset["data"], spec)

        self.assertEqual(len(signal), len(dataset["data"]))
        self.assertTrue(set(signal.unique()).issubset({0, 1}))
        self.assertEqual(signal.iloc[-1], 1)

    def test_search_keeps_one_champion_per_round(self):
        report = run_random_strategy_search([self._dataset()], rounds=3, seed=7)

        self.assertEqual(report["rounds"], 3)
        self.assertEqual(len(report["history"]), 3)
        self.assertIn("champion", report)
        self.assertIn("spec", report["champion"])
        self.assertEqual(len(report["history"][0]["candidates"]), 10)
        self.assertEqual(len(report["history"][1]["candidates"]), 10)


if __name__ == "__main__":
    unittest.main()
