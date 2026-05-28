import inspect
import unittest
from pathlib import Path

from core.data_fetcher import DataFetcher
from core.fund_api import fetch_fund_nav
from scripts.refresh_max_history import Target, _parse_cache_name


class MaxHistoryDefaultsTest(unittest.TestCase):
    def test_data_fetch_defaults_to_max_history(self):
        fetch_period = inspect.signature(DataFetcher.fetch).parameters["period"].default
        fund_period = inspect.signature(fetch_fund_nav).parameters["period"].default

        self.assertEqual(fetch_period, "max")
        self.assertEqual(fund_period, "max")

    def test_refresh_script_discovers_existing_cache_names(self):
        self.assertEqual(
            _parse_cache_name(Path("fund_002982_1y_1d.csv")),
            Target(market="fund", symbol="002982"),
        )
        self.assertEqual(
            _parse_cache_name(Path("us_stock_NVDA_max_1d.csv")),
            Target(market="us_stock", symbol="NVDA"),
        )

    def test_windows_auto_refresh_task_script_exists(self):
        script = Path("setup_max_history_refresh_task.ps1")
        content = script.read_text(encoding="utf-8")

        self.assertIn("QuantMaxHistoryRefresh", content)
        self.assertIn("refresh_max_history.py", content)
        self.assertIn("max_history_refresh.log", content)


if __name__ == "__main__":
    unittest.main()
