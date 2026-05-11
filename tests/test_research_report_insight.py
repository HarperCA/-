import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from web_modules.research_report import build_report_from_upload, metrics_from_frame


def test_small_capital_report_sections_and_no_direct_trade_advice():
    df = pd.DataFrame({
        "date": pd.date_range("2025-01-01", periods=90, freq="D"),
        "nav": [1 + i * 0.001 for i in range(60)] + [1.06 - i * 0.002 for i in range(30)],
    })

    report = build_report_from_upload(df, "demo_nav.csv")
    markdown = report["markdown"]

    assert "## 一句话结论" in markdown
    assert "## 数据可信度" in markdown
    assert "## 关键发现" in markdown
    assert "## 回撤与风险" in markdown
    assert "## 小资金用户注意事项" in markdown
    assert "## 落地结论" in markdown
    assert "## 执行清单" in markdown
    assert "## 资料来源与引用" in markdown
    assert "## 建议追问" in markdown
    assert "行情时间：2025-03-31" in markdown
    assert "系统获取时间：" in markdown
    assert report["market_time"] == "2025-03-31"
    assert report["system_fetch_time"]
    assert "买入" not in markdown
    assert "卖出" not in markdown


def test_holdings_table_without_return_series_still_generates_report():
    df = pd.DataFrame({
        "symbol": ["A", "B", "C"],
        "quantity": [100, 200, 300],
        "avg_cost": [10, 8, 3],
        "weight": [0.55, 0.30, 0.15],
    })

    metrics = metrics_from_frame(df)
    report = build_report_from_upload(df, "holdings.csv")
    markdown = report["markdown"]

    assert metrics["data_type"] == "持仓表"
    assert metrics["has_return_series"] is False
    assert "补充净值/收益率字段" in markdown
    assert "集中度" in markdown
    assert "当前数据不足，只能作为数据验收" in markdown
    assert "当前不能直接用于投资决策" in markdown
    assert "## 资料来源与引用" in markdown
    assert "行情时间：未识别" in markdown
    assert "系统获取时间：" in markdown
    assert "买入" not in markdown
    assert "卖出" not in markdown
