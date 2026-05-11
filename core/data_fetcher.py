"""
数据获取模块
支持 A股(akshare)、美股(yfinance)、加密货币(yfinance/ccxt)、中国场外基金(akshare)
"""
from __future__ import annotations

import pandas as pd
import yfinance as yf
import os
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path


@contextmanager
def _without_proxy():
    proxy_keys = [
        "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
        "http_proxy", "https_proxy", "all_proxy",
    ]
    old_values = {key: os.environ.get(key) for key in proxy_keys}
    old_no_proxy = os.environ.get("NO_PROXY")
    try:
        for key in proxy_keys:
            os.environ.pop(key, None)
        no_proxy_hosts = [
            "eastmoney.com", ".eastmoney.com",
            "push2his.eastmoney.com", "api.fund.eastmoney.com",
        ]
        os.environ["NO_PROXY"] = ",".join(filter(None, [old_no_proxy, *no_proxy_hosts]))
        yield
    finally:
        for key, value in old_values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        if old_no_proxy is None:
            os.environ.pop("NO_PROXY", None)
        else:
            os.environ["NO_PROXY"] = old_no_proxy


class DataFetcher:
    """统一数据获取接口"""

    def __init__(self, source: str = "akshare"):
        self.source = source
        self.cache_dir = Path(__file__).resolve().parent.parent / "data" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        if source == "akshare":
            try:
                import akshare as ak
                self.ak = ak
            except ImportError:
                raise ImportError("请先安装 akshare: pip install akshare")

    def fetch(
        self,
        symbol: str,
        market: str = "a_stock",
        period: str = "max",
        interval: str = "1d",
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """
        获取历史K线数据

        参数:
            symbol: 标的代码，如 '000001'（A股）、'000001'（基金）、'BTC-USD'（加密货币）
            market: 市场类型: a_stock / us_stock / crypto / fund
            period: 时间范围: 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
            interval: K线周期: 1d, 1wk, 1mo

        返回:
            DataFrame，列: open, high, low, close, volume
        """
        cache_path = self._cache_path(symbol, market, period, interval)
        cached = self._read_cache(cache_path)
        if not force_refresh and cached is not None and self._cache_is_fresh(cache_path):
            print(f"   使用缓存数据: {cache_path.name}")
            return self._normalize_ohlcv(cached, symbol=symbol, market=market)

        try:
            if market == "a_stock":
                df = self._fetch_a_stock(symbol, period, interval)
            elif market == "fund":
                df = self._fetch_fund(symbol, period)
            elif market == "us_stock":
                df = self._fetch_us_stock(symbol, period, interval)
            elif market == "crypto":
                df = self._fetch_yfinance(symbol, period, interval)
            else:
                raise ValueError(f"不支持的市场类型: {market}")
        except Exception:
            if cached is not None:
                print(f"   数据源暂不可用，使用旧缓存: {cache_path.name}")
                return self._normalize_ohlcv(cached, symbol=symbol, market=market)
            raise

        df = self._normalize_ohlcv(df, symbol=symbol, market=market)
        self._write_cache(cache_path, df)
        return df

    def _normalize_ohlcv(self, df: pd.DataFrame, symbol: str, market: str) -> pd.DataFrame:
        if df is None or df.empty:
            raise RuntimeError(f"未获取到 {market} {symbol} 的有效数据")

        out = df.copy()
        if not isinstance(out.index, pd.DatetimeIndex):
            out.index = pd.to_datetime(out.index, errors="coerce")
        out = out[~out.index.isna()]
        out = out[~out.index.duplicated(keep="last")].sort_index()

        required = ["open", "high", "low", "close", "volume"]
        missing = [col for col in required if col not in out.columns]
        if missing:
            raise RuntimeError(f"{market} {symbol} 数据缺少字段: {', '.join(missing)}")

        for col in required:
            out[col] = pd.to_numeric(out[col], errors="coerce")

        out[required] = out[required].replace([float("inf"), float("-inf")], pd.NA)
        price_cols = ["open", "high", "low", "close"]
        out = out.dropna(subset=price_cols)
        out = out[(out[price_cols] > 0).all(axis=1)]
        out["volume"] = out["volume"].fillna(0).clip(lower=0)
        if out.empty:
            raise RuntimeError(f"{market} {symbol} 清洗后没有有效价格数据")

        out["high"] = out[["open", "high", "close"]].max(axis=1)
        out["low"] = out[["open", "low", "close"]].min(axis=1)
        return out[required]

    def _cache_path(self, symbol: str, market: str, period: str, interval: str) -> Path:
        safe_symbol = "".join(ch if ch.isalnum() else "_" for ch in str(symbol).upper())
        safe_market = "".join(ch if ch.isalnum() else "_" for ch in str(market))
        safe_period = "".join(ch if ch.isalnum() else "_" for ch in str(period))
        safe_interval = "".join(ch if ch.isalnum() else "_" for ch in str(interval))
        return self.cache_dir / f"{safe_market}_{safe_symbol}_{safe_period}_{safe_interval}.csv"

    def _cache_is_fresh(self, cache_path: Path, max_age_hours: int = 6) -> bool:
        if not cache_path.exists():
            return False
        age_seconds = time.time() - cache_path.stat().st_mtime
        return age_seconds <= max_age_hours * 3600

    def _read_cache(self, cache_path: Path) -> pd.DataFrame | None:
        if not cache_path.exists():
            return None
        try:
            df = pd.read_csv(cache_path, parse_dates=["date"])
            df = df.set_index("date")
            return df[["open", "high", "low", "close", "volume"]]
        except Exception:
            return None

    def _write_cache(self, cache_path: Path, df: pd.DataFrame) -> None:
        try:
            out = df[["open", "high", "low", "close", "volume"]].copy()
            out.index.name = "date"
            out.to_csv(cache_path, encoding="utf-8")
        except Exception:
            pass

    def _fetch_a_stock(
        self, symbol: str, period: str, interval: str
    ) -> pd.DataFrame:
        """通过 akshare 获取A股数据"""
        # 转换时间周期为 akshare 格式
        end_date = datetime.now().strftime("%Y%m%d")
        period_map = {
            "1mo": 30, "3mo": 90, "6mo": 180,
            "1y": 365, "2y": 730, "3y": 1095, "5y": 1825,
            "10y": 3650, "20y": 7300, "50y": 18250,
            "max": 36500,
        }
        days = period_map.get(period, 365)
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

        # 自动补全后缀
        if not (symbol.endswith(".SH") or symbol.endswith(".SZ")):
            if symbol.startswith("6"):
                symbol += ".SH"
            else:
                symbol += ".SZ"

        last_error = None
        for attempt in range(3):
            try:
                with _without_proxy():
                    df = self.ak.stock_zh_a_hist(
                        symbol=symbol.replace(".SH", "").replace(".SZ", ""),
                        period=interval.replace("1d", "daily").replace("1wk", "weekly"),
                        start_date=start_date,
                        end_date=end_date,
                        adjust="qfq",  # 前复权
                    )
                break
            except Exception as exc:
                last_error = exc
                time.sleep(0.8 * (attempt + 1))
        else:
            raise RuntimeError(f"A股数据源连接失败: {last_error}")

        if df is None or df.empty:
            raise RuntimeError(f"未获取到 A股 {symbol} 的数据")
        df = df.rename(columns={
            "日期": "date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
        })
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        df = df[["open", "high", "low", "close", "volume"]]
        return df

    def _fetch_yfinance(
        self, symbol: str, period: str, interval: str
    ) -> pd.DataFrame:
        """通过 yfinance 获取美股/加密货币数据"""
        ticker = yf.Ticker(symbol)
        if period in ("20y", "50y"):
            years = int(period.replace("y", ""))
            start = (datetime.now() - timedelta(days=365 * years)).strftime("%Y-%m-%d")
            df = ticker.history(start=start, interval=interval)
        elif period == "max":
            df = ticker.history(period="max", interval=interval)
        else:
            df = ticker.history(period=period, interval=interval)
        df.index = df.index.tz_localize(None)  # 去除时区
        df.columns = [c.lower().replace("stock splits", "splits") for c in df.columns]
        return df[["open", "high", "low", "close", "volume"]]

    def _fetch_us_stock(
        self, symbol: str, period: str, interval: str
    ) -> pd.DataFrame:
        """获取美股数据，yfinance 限流时使用 Stooq 日线数据兜底。"""
        try:
            return self._fetch_yfinance(symbol, period, interval)
        except Exception as exc:
            if interval != "1d":
                raise
            print(f"   yfinance 暂不可用，切换 Stooq 备用源: {exc}")
            return self._fetch_us_stock_stooq(symbol, period)

    def _fetch_us_stock_stooq(self, symbol: str, period: str) -> pd.DataFrame:
        period_map = {
            "1mo": 30, "3mo": 90, "6mo": 180,
            "1y": 365, "2y": 730, "3y": 1095, "5y": 1825,
            "10y": 3650, "20y": 7300, "50y": 18250,
            "max": 36500,
        }
        days = period_map.get(period, 365)
        start = datetime.now() - timedelta(days=days)
        stooq_symbol = symbol.lower()
        if "." not in stooq_symbol:
            stooq_symbol = f"{stooq_symbol}.us"
        url = f"https://stooq.com/q/d/l/?s={stooq_symbol}&i=d"
        df = pd.read_csv(url)
        if df is None or df.empty:
            raise RuntimeError(f"Stooq 未获取到美股 {symbol} 的数据")
        df = df.rename(columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        })
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).set_index("date").sort_index()
        df = df[df.index >= start]
        return df[["open", "high", "low", "close", "volume"]]

    def _fetch_fund(self, symbol: str, period: str) -> pd.DataFrame:
        """获取中国场外基金历史净值（使用东方财富 API）"""
        from core.fund_api import fetch_fund_nav
        return fetch_fund_nav(symbol, period)

    @staticmethod
    def format_symbol(symbol: str, market: str) -> str:
        """格式化代码，方便不同市场统一"""
        if market in ("a_stock", "fund"):
            return symbol.zfill(6)
        return symbol.upper()
