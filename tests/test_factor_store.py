import tempfile
import unittest
from pathlib import Path

import pandas as pd

from core.factor_store import (
    FactorStore,
    FactorSpec,
    build_market_factors,
    import_external_factor_frame,
    import_market_factor_frame,
    register_all_factors,
)


class FactorStoreTest(unittest.TestCase):
    def test_register_import_and_query_market_factors(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FactorStore(Path(tmp) / "factors.sqlite")
            register_all_factors(store)

            dates = pd.date_range("2026-01-01", periods=30, freq="D")
            close_a = pd.Series(range(100, 130), dtype=float)
            close_b = pd.Series(range(90, 150, 2), dtype=float)
            factors = pd.concat(
                [
                    build_market_factors(self._market_df(dates, close_a, 1000), symbol="000001"),
                    build_market_factors(self._market_df(dates, close_b, 2000), symbol="000002"),
                ],
                ignore_index=True,
            )
            imported = import_market_factor_frame(store, factors, market="a_stock")

            self.assertGreater(imported, 0)
            definitions = store.list_factors()
            self.assertIn("momentum_20d", set(definitions["factor_name"]))
            self.assertIn("pe_ttm", set(definitions["factor_name"]))

            rows = store.get_factor_values(
                ["momentum_20d", "volatility_20d"],
                symbols=["000001"],
                market="a_stock",
                start_date="2026-01-20",
                pivot=True,
            )

            self.assertIn("momentum_20d", rows.columns)
            self.assertIn("volatility_20d", rows.columns)
            self.assertTrue(rows["momentum_20d"].notna().any())

            matrix = store.get_factor_matrix(
                ["momentum_20d", "volatility_20d"],
                market="a_stock",
                date="2026-01-30",
                value_column="rank_pct",
            )
            self.assertEqual(len(matrix), 2)
            self.assertIn("momentum_20d", matrix.columns)

            store.upsert_evaluation(
                "momentum_20d",
                eval_date="2026-01-30",
                market="a_stock",
                horizon="5d",
                ic=0.12,
                rank_ic=0.08,
                sample_size=2,
            )
            quality = store.list_quality("a_stock")
            self.assertFalse(quality.empty)

    def test_import_external_factor_frame(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FactorStore(Path(tmp) / "factors.sqlite")
            frame = pd.DataFrame(
                {
                    "trade_date": ["2026-01-02", "2026-01-02"],
                    "symbol": ["000001", "000002"],
                    "industry": ["bank", "bank"],
                    "pe_ttm": [6.2, 9.1],
                }
            )
            rows = import_external_factor_frame(
                store,
                frame,
                FactorSpec("pe_ttm", "valuation", "PE TTM", source="fundamental"),
                market="a_stock",
            )

            self.assertEqual(rows, 2)
            loaded = store.get_factor_values(["pe_ttm"], market="a_stock")
            self.assertEqual(set(loaded["industry"]), {"bank"})
            self.assertTrue(loaded["rank_pct"].notna().all())

    def _market_df(self, dates, close, volume):
        return pd.DataFrame(
            {
                "date": dates,
                "open": close,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "volume": volume,
            }
        )


if __name__ == "__main__":
    unittest.main()
