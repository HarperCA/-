import unittest

import pandas as pd

from core.data_fetcher import DataFetcher


class DataFetcherQualityTest(unittest.TestCase):
    def test_normalize_ohlcv_drops_invalid_prices_and_clips_negative_volume(self):
        dates = pd.date_range("2025-01-01", periods=4, freq="D")
        raw = pd.DataFrame(
            {
                "open": [10.0, -1.0, 12.0, 13.0],
                "high": [9.0, 11.0, float("inf"), 14.0],
                "low": [8.0, 9.0, 10.0, 12.0],
                "close": [10.5, 10.0, 12.5, 13.5],
                "volume": [-100, 200, 300, None],
            },
            index=dates,
        )

        normalized = DataFetcher(source="test")._normalize_ohlcv(raw, symbol="T", market="test")

        self.assertEqual(len(normalized), 2)
        self.assertEqual(normalized["volume"].tolist(), [0.0, 0.0])
        self.assertTrue((normalized[["open", "high", "low", "close"]] > 0).all().all())
        self.assertGreaterEqual(normalized["high"].iloc[0], normalized["close"].iloc[0])


if __name__ == "__main__":
    unittest.main()
