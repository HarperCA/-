import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from web_modules.research_report import build_report_from_upload
from web_modules.source_records import (
    apply_data_breadth,
    failed_record,
    record,
    source_reliability_penalty,
    upload_source_record,
)


def test_source_record_shape_and_report_reference_section(tmp_path):
    csv_path = tmp_path / "holdings.csv"
    df = pd.DataFrame({"symbol": ["A", "B"], "quantity": [100, 200], "avg_cost": [10, 8]})
    df.to_csv(csv_path, index=False)

    source = upload_source_record(csv_path, df, "holdings.csv")
    report = build_report_from_upload(df, "holdings.csv", source_records=[source])

    assert source.to_dict()["source_type"] == "user_upload"
    assert source.to_dict()["source_name"] == "用户上传文件"
    assert "## 资料来源与引用" in report["markdown"]
    assert "用户上传文件" in report["markdown"]
    assert "计算持仓结构与集中度" in report["markdown"]
    assert report["source_records"][0]["fields"] == ["symbol", "quantity", "avg_cost"]


def test_data_breadth_standard_adds_local_context_and_failures(tmp_path):
    user_dir = tmp_path / "user"
    reports_dir = user_dir / "research_reports"
    user_dir.mkdir()
    reports_dir.mkdir()
    (user_dir / "holdings.json").write_text(json.dumps([{"symbol": "000001", "weight": 0.5}]), encoding="utf-8")
    (user_dir / "analysis_history.json").write_text(json.dumps([{"symbol": "000001", "market": "a_stock"}]), encoding="utf-8")
    (reports_dir / "research_demo.json").write_text(json.dumps({"title": "旧报告", "sections": {"报告摘要": []}}), encoding="utf-8")

    records = apply_data_breadth(
        [record("user_upload", "用户上传文件", "demo.csv", fields=["date", "nav"], used_for="收益计算", reliability="high")],
        breadth="标准",
        user_path=user_dir,
        reports_path=reports_dir,
        db_path=tmp_path / "missing.sqlite",
        cache_dir=tmp_path / "cache",
        symbol="000001",
        market="a_stock",
        period="1y",
    )
    payload = [item.to_dict() for item in records]
    types = {item["source_type"] for item in payload}

    assert "user_upload" in types
    assert "market_data" in types
    assert "user_holdings" in types
    assert "analysis_history" in types
    assert "generated_report" in types
    assert any("未获取到" in item["notes"] for item in payload)


def test_failed_sources_lower_confidence():
    penalty = source_reliability_penalty([
        failed_record("news", "新闻接口", "公告资料", used_for="波动解释", error="network unavailable")
    ])

    assert penalty > 0
