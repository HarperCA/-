#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit whether a generated research report is backed by traceable data."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

import pandas as pd


def find_latest_report(root: Path) -> Path:
    reports = sorted(root.glob("data/userspace/*/research_reports/research_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not reports:
        raise FileNotFoundError("No research report JSON files found under data/userspace.")
    return reports[0]


def audit_report(report_path: Path, root: Path) -> dict:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    sources = report.get("source_records") or report.get("sources") or []
    findings: list[dict] = []
    status = "pass"

    if not sources:
        return {
            "report": str(report_path),
            "title": report.get("title"),
            "status": "fail",
            "findings": [{
                "level": "high",
                "message": "报告没有 source_records/sources，无法验证分析数据是否真实可追溯。",
            }],
        }

    for source in sources:
        source_type = source.get("source_type")
        notes = source.get("notes", "")
        reliability = source.get("reliability", "medium")
        if reliability == "low" or "未获取到" in notes:
            status = "warn" if status == "pass" else status
            findings.append({
                "level": "medium",
                "message": f"来源 {source.get('title')} 可靠性较低或获取失败：{notes}",
            })

        if source_type == "user_upload":
            result = audit_uploaded_source(source, root)
            findings.extend(result["findings"])
            if result["status"] == "fail":
                status = "fail"
            elif result["status"] == "warn" and status == "pass":
                status = "warn"
        elif source_type in {"sqlite"}:
            result = audit_sqlite_source(source, root)
            findings.extend(result["findings"])
            if result["status"] == "fail":
                status = "fail"
            elif result["status"] == "warn" and status == "pass":
                status = "warn"
        elif source_type in {"cache"}:
            result = audit_cache_source(source, root)
            findings.extend(result["findings"])
            if result["status"] == "fail":
                status = "fail"
            elif result["status"] == "warn" and status == "pass":
                status = "warn"

    return {
        "report": str(report_path),
        "title": report.get("title"),
        "generated_at": report.get("generated_at"),
        "subject": report.get("subject"),
        "status": status,
        "source_count": len(sources),
        "findings": findings,
    }


def audit_uploaded_source(source: dict, root: Path) -> dict:
    findings = []
    status = "pass"
    filename = extract_note_value(source.get("notes", ""), "文件")
    if not filename:
        return {"status": "warn", "findings": [{"level": "medium", "message": f"用户上传来源缺少文件名：{source}"}]}
    matches = list(root.glob(f"data/userspace/**/{filename}"))
    if not matches:
        return {"status": "fail", "findings": [{"level": "high", "message": f"用户上传文件不存在：{filename}"}]}

    path = matches[0]
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except Exception as exc:
        return {"status": "fail", "findings": [{"level": "high", "message": f"无法读取用户上传文件 {path}: {exc}"}]}

    expected_fields = set(source.get("fields") or [])
    actual_fields = set(map(str, df.columns))
    missing = expected_fields - actual_fields
    if missing:
        status = "warn"
        findings.append({"level": "medium", "message": f"上传文件字段与报告记录不一致，缺少：{sorted(missing)}"})
    if len(df) < 20:
        status = "warn"
        findings.append({"level": "medium", "message": f"上传文件只有 {len(df)} 行，样本过少，只能视为测试/预览数据。"})
    findings.append({"level": "info", "message": f"用户上传文件可追溯：{path}，行数 {len(df)}，字段 {list(df.columns)}"})
    return {"status": status, "findings": findings}


def audit_sqlite_source(source: dict, root: Path) -> dict:
    db_path = root / "data/quant_app.sqlite"
    if not db_path.exists():
        return {"status": "fail", "findings": [{"level": "high", "message": "SQLite 数据库不存在：data/quant_app.sqlite"}]}
    try:
        conn = sqlite3.connect(db_path)
        try:
            tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        finally:
            conn.close()
    except Exception as exc:
        return {"status": "fail", "findings": [{"level": "high", "message": f"SQLite 无法打开：{exc}"}]}
    return {"status": "pass", "findings": [{"level": "info", "message": f"SQLite 可打开，表数量 {len(tables)}。"}]}


def audit_cache_source(source: dict, root: Path) -> dict:
    file_match = re.search(r"文件：([^；]+)", source.get("notes", ""))
    if not file_match:
        return {"status": "warn", "findings": [{"level": "medium", "message": f"缓存来源缺少可核对文件路径：{source.get('title')}"}]}
    path = root / file_match.group(1)
    if not path.exists():
        return {"status": "fail", "findings": [{"level": "high", "message": f"缓存文件不存在：{path}"}]}
    return {"status": "pass", "findings": [{"level": "info", "message": f"缓存文件存在：{path}，大小 {path.stat().st_size} 字节。"}]}


def extract_note_value(notes: str, key: str) -> str | None:
    match = re.search(rf"{re.escape(key)}：([^；]+)", notes)
    return match.group(1) if match else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit generated report source traceability.")
    parser.add_argument("--report", help="Path to research_*.json. Defaults to latest report.")
    parser.add_argument("--root", default=".", help="Project root.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = Path(args.report) if args.report else find_latest_report(root)
    if not report.is_absolute():
        report = root / report
    result = audit_report(report, root)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
