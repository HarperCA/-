"""
中国场外基金数据获取（直接调用东方财富 API）
不依赖 akshare 的具体接口版本
"""
import requests
import pandas as pd
import time
from datetime import datetime, timedelta


def fetch_fund_nav(fund_code: str, period: str = "max") -> pd.DataFrame:
    """
    通过东方财富 API 获取基金历史净值
    """
    period_map = {
        "1mo": 30, "3mo": 90, "6mo": 180,
        "1y": 365, "2y": 730, "3y": 1095, "5y": 1825,
        "10y": 3650, "20y": 7300, "50y": 18250,
        "max": 36500,
    }
    days = period_map.get(period, 365)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    all_records = []
    page = 1
    page_size = 20
    max_pages = 1000

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"http://fundf10.eastmoney.com/jjjz_{fund_code}.html",
    }
    session = requests.Session()
    session.trust_env = False

    while page <= max_pages:
        url = (
            f"http://api.fund.eastmoney.com/f10/lsjz"
            f"?fundCode={fund_code}"
            f"&pageIndex={page}"
            f"&pageSize={page_size}"
            f"&startDate={start_date.strftime('%Y-%m-%d')}"
            f"&endDate={end_date.strftime('%Y-%m-%d')}"
        )

        last_error = None
        for attempt in range(3):
            try:
                resp = session.get(
                    url,
                    headers=headers,
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
                break
            except Exception as e:
                last_error = e
                time.sleep(0.8 * (attempt + 1))
        else:
            raise RuntimeError(f"请求东方财富 API 失败: {last_error}")

        if data.get("ErrCode") != 0:
            raise RuntimeError(f"API 返回错误: {data.get('ErrMsg', '未知错误')}")

        items = data.get("Data", {}).get("LSJZList", [])
        if not items:
            break

        for item in items:
            all_records.append({
                "date": item.get("FSRQ"),
                "nav": item.get("DWJZ"),
                "acc_nav": item.get("LJJZ"),
                "daily_change": item.get("JZZZL"),
            })

        if len(items) < page_size:
            break
        page += 1

    if not all_records:
        raise RuntimeError(f"未获取到基金 {fund_code} 的数据")

    df = pd.DataFrame(all_records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()

    # 构造 OHLC（基金只有净值）
    df["close"] = pd.to_numeric(df["nav"], errors="coerce")
    df["open"] = df["close"].shift(1).fillna(df["close"])
    df["high"] = df[["open", "close"]].max(axis=1)
    df["low"] = df[["open", "close"]].min(axis=1)
    df["volume"] = 0

    return df[["open", "high", "low", "close", "volume"]]
