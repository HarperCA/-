import sys
import types
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.realtime_data import fetch_a_stock_spot, fetch_fund_estimate, fetch_yfinance_spot
from web_modules.source_records import apply_data_breadth, realtime_quote_source_record


def test_fetch_a_stock_spot_from_akshare_mock(monkeypatch):
    fake_ak = types.SimpleNamespace(
        stock_zh_a_spot_em=lambda: pd.DataFrame(
            [{"代码": "000001", "名称": "平安银行", "最新价": 10.5, "涨跌幅": 1.2, "成交量": 1000}]
        )
    )
    monkeypatch.setitem(sys.modules, "akshare", fake_ak)

    quote = fetch_a_stock_spot("000001")

    assert quote.symbol == "000001"
    assert quote.price == 10.5
    assert quote.source == "AkShare / 东方财富实时行情"


def test_fetch_yfinance_spot_from_history_mock():
    index = pd.to_datetime(["2026-05-10 10:00", "2026-05-10 10:01"])
    history = pd.DataFrame({"Close": [100.0, 101.0], "Volume": [10, 20]}, index=index)
    fake_ticker = Mock()
    fake_ticker.history.return_value = history

    with patch("core.realtime_data.yf.Ticker", return_value=fake_ticker):
        quote = fetch_yfinance_spot("AAPL", "us_stock")

    assert quote.symbol == "AAPL"
    assert quote.price == 101.0
    assert quote.volume == 20.0
    assert quote.source == "yfinance"


def test_fetch_fund_estimate_from_eastmoney_jsonp_mock():
    fake_response = Mock()
    fake_response.text = 'jsonpgz({"fundcode":"002982","name":"基金","gsz":"1.234","gszzl":"0.56","gztime":"2026-05-10 10:00"});'
    fake_response.raise_for_status.return_value = None
    fake_session = Mock()
    fake_session.get.return_value = fake_response

    with patch("core.realtime_data.requests.Session", return_value=fake_session):
        quote = fetch_fund_estimate("002982")

    assert quote.symbol == "002982"
    assert quote.price == 1.234
    assert quote.change_pct == 0.56
    assert "东方财富" in quote.source


def test_realtime_quote_source_record_contains_timestamps():
    index = pd.to_datetime(["2026-05-10 10:01"])
    history = pd.DataFrame({"Close": [101.0], "Volume": [20]}, index=index)
    fake_ticker = Mock()
    fake_ticker.history.return_value = history

    with patch("core.realtime_data.yf.Ticker", return_value=fake_ticker):
        quote = fetch_yfinance_spot("AAPL", "us_stock")

    source = realtime_quote_source_record(quote).to_dict()
    assert source["source_type"] == "realtime_quote"
    assert "最新价格快照" in source["used_for"]
    assert "系统获取时间" in source["notes"]


def test_apply_data_breadth_degrades_when_realtime_fails(tmp_path):
    with patch("web_modules.source_records.fetch_realtime_quote", side_effect=RuntimeError("network down")):
        records = apply_data_breadth(
            [],
            breadth="标准",
            user_path=tmp_path,
            reports_path=tmp_path,
            db_path=tmp_path / "missing.sqlite",
            cache_dir=tmp_path,
            symbol="AAPL",
            market="us_stock",
            period="1d",
        )

    payload = [item.to_dict() for item in records]
    realtime = [item for item in payload if item["source_type"] == "realtime_quote"]
    assert realtime
    assert realtime[0]["reliability"] == "low"
