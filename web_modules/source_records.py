# -*- coding: utf-8 -*-
"""Source records and lightweight source collection for research reports."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from core.realtime_data import QuoteSnapshot, fetch_realtime_quote


@dataclass
class SourceRecord:
    source_type: str
    source_name: str
    title: str
    url: str | None
    retrieved_at: str
    fields: list[str]
    used_for: str
    reliability: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def record(
    source_type: str,
    source_name: str,
    title: str,
    *,
    fields: list[str] | None = None,
    used_for: str,
    reliability: str = "medium",
    url: str | None = None,
    notes: str = "",
) -> SourceRecord:
    return SourceRecord(
        source_type=source_type,
        source_name=source_name,
        title=title,
        url=url,
        retrieved_at=now_text(),
        fields=fields or [],
        used_for=used_for,
        reliability=reliability,
        notes=notes,
    )


def failed_record(
    source_type: str,
    source_name: str,
    title: str,
    *,
    used_for: str,
    error: Exception | str,
) -> SourceRecord:
    return record(
        source_type,
        source_name,
        title,
        used_for=used_for,
        reliability="low",
        notes=f"未获取到：{error}",
    )


def source_dicts(records: list[SourceRecord | dict]) -> list[dict[str, Any]]:
    out = []
    for item in records:
        out.append(item.to_dict() if isinstance(item, SourceRecord) else dict(item))
    return out


def realtime_quote_source_record(snapshot: QuoteSnapshot | dict) -> SourceRecord:
    data = snapshot.to_dict() if hasattr(snapshot, "to_dict") else dict(snapshot)
    fields = [
        "symbol",
        "market",
        "price",
        "change_pct",
        "volume",
        "quote_time",
        "retrieved_at",
    ]
    notes = (
        f"最新价：{data.get('price', '-')}; 涨跌幅：{data.get('change_pct', '-')}; "
        f"行情时间：{data.get('quote_time') or '-'}; 系统获取时间：{data.get('retrieved_at')}; "
        f"{data.get('notes', '')}"
    )
    return record(
        "realtime_quote",
        str(data.get("source") or "准实时行情源"),
        f"{data.get('symbol', '-')} 准实时行情快照",
        fields=fields,
        used_for="最新价格快照 / 风险预警 / 报告生成时点引用",
        reliability=str(data.get("reliability") or "medium"),
        notes=notes,
    )


def realtime_quote_records(symbol: str, market: str) -> list[SourceRecord]:
    try:
        snapshot = fetch_realtime_quote(symbol, market)
        return [realtime_quote_source_record(snapshot)]
    except Exception as exc:
        return [
            failed_record(
                "realtime_quote",
                "AkShare / yfinance / 东方财富",
                f"{symbol} 准实时行情快照",
                used_for="最新价格快照 / 风险预警 / 报告生成时点引用",
                error=exc,
            )
        ]


def upload_source_record(path: Path, df: pd.DataFrame, original_name: str | None = None) -> SourceRecord:
    return record(
        "user_upload",
        "用户上传文件",
        original_name or path.name,
        fields=[str(col) for col in df.columns],
        used_for="收益计算 / 回撤分析 / 计算持仓结构与集中度",
        reliability="high",
        notes=f"文件：{path.name}；行数：{len(df)}；系统只基于用户提供内容计算，不补造缺失字段。",
    )


def holdings_source_record(path: Path) -> SourceRecord:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            rows = sum(len(v) for v in data.values() if isinstance(v, list))
            fields = sorted({str(k) for v in data.values() if isinstance(v, list) for row in v if isinstance(row, dict) for k in row})
        elif isinstance(data, list):
            rows = len(data)
            fields = sorted({str(k) for row in data if isinstance(row, dict) for k in row})
        else:
            rows = 0
            fields = []
        return record(
            "user_holdings",
            "本地用户持仓",
            "用户持仓文件",
            fields=fields,
            used_for="组合集中度 / 持仓结构 / 风险暴露复核",
            reliability="high",
            notes=f"文件：{path.name}；记录数：{rows}",
        )
    except Exception as exc:
        return failed_record("user_holdings", "本地用户持仓", "用户持仓文件", used_for="组合集中度复核", error=exc)


def history_source_record(path: Path) -> SourceRecord:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = len(data) if isinstance(data, list) else 0
        fields = sorted({str(k) for row in data if isinstance(row, dict) for k in row}) if isinstance(data, list) else []
        return record(
            "analysis_history",
            "本地历史分析",
            "历史分析记录",
            fields=fields,
            used_for="复盘对照 / 已生成结论追踪 / 报告版本回溯",
            reliability="medium",
            notes=f"文件：{path.name}；记录数：{rows}",
        )
    except Exception as exc:
        return failed_record("analysis_history", "本地历史分析", "历史分析记录", used_for="复盘对照", error=exc)


def sqlite_source_record(path: Path) -> SourceRecord:
    try:
        conn = sqlite3.connect(path)
        try:
            tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        finally:
            conn.close()
        return record(
            "sqlite",
            "SQLite 本地数据库",
            "quant_app.sqlite",
            fields=tables,
            used_for="用户记录镜像 / 因子库 / 报告资料索引",
            reliability="medium",
            notes=f"数据库：{path.as_posix()}；表数量：{len(tables)}",
        )
    except Exception as exc:
        return failed_record("sqlite", "SQLite 本地数据库", "quant_app.sqlite", used_for="本地结构化资料", error=exc)


def cache_source_record(path: Path, *, symbol: str | None = None, market: str | None = None) -> SourceRecord:
    try:
        df = pd.read_csv(path, nrows=5, encoding="utf-8-sig")
        mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        return record(
            "cache",
            "本地缓存",
            path.name,
            fields=[str(col) for col in df.columns],
            used_for="行情兜底 / 历史净值、收益、回撤计算",
            reliability="medium",
            notes=f"文件：{path.as_posix()}；缓存时间：{mtime}；标的：{symbol or '-'}；市场：{market or '-'}",
        )
    except Exception as exc:
        return failed_record("cache", "本地缓存", path.name, used_for="行情兜底", error=exc)


def generated_report_source_record(path: Path) -> SourceRecord:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return record(
            "generated_report",
            "已生成报告",
            data.get("title") or path.name,
            fields=list((data.get("sections") or {}).keys()),
            used_for="历史报告引用 / 结论版本追踪",
            reliability="medium",
            notes=f"报告文件：{path.name}；生成时间：{data.get('generated_at', '-')}",
        )
    except Exception as exc:
        return failed_record("generated_report", "已生成报告", path.name, used_for="历史报告引用", error=exc)


def market_source_records(symbol: str, market: str, period: str, *, cache_dir: Path, data_range: str | None = None) -> list[SourceRecord]:
    source_name = "AkShare" if market in {"a_stock", "fund"} else "yfinance"
    title = f"{symbol} 行情数据"
    used_for = "历史净值、收益、回撤、波动与趋势状态计算"
    records = [
        record(
            "market_data",
            source_name,
            title,
            fields=["date", "open", "high", "low", "close", "volume"],
            used_for=used_for,
            reliability="high",
            notes=f"市场：{market}；区间：{data_range or period}；如网络不可用则使用本地缓存兜底。",
        )
    ]
    safe_symbol = "".join(ch if ch.isalnum() else "_" for ch in str(symbol).upper())
    patterns = [f"*{safe_symbol}*.csv", f"*{str(symbol).upper()}*.csv", f"*{str(symbol)}*.csv"]
    seen: set[Path] = set()
    for pattern in patterns:
        for path in cache_dir.glob(pattern):
            if path in seen:
                continue
            seen.add(path)
            records.append(cache_source_record(path, symbol=symbol, market=market))
    if not seen:
        records.append(
            record(
                "cache",
                "本地缓存",
                f"{symbol} 缓存文件",
                used_for="行情兜底",
                reliability="low",
                notes="未找到匹配缓存文件；若远程行情获取失败，相关结论置信度需要降低。",
            )
        )
    if market == "fund":
        records.append(
            record(
                "fund_profile",
                "东方财富基金接口",
                f"{symbol} 基金基础资料",
                fields=["基金经理", "基金类型", "规模", "费率", "净值"],
                used_for="补充标的背景 / 基金资料解释",
                reliability="medium",
                notes="通过项目内东方财富基金接口或 AkShare 基金数据链路获取；失败时不阻断报告。",
            )
        )
    elif market in {"a_stock", "us_stock"}:
        records.append(
            record(
                "stock_profile",
                "AkShare / yfinance",
                f"{symbol} 股票基础资料",
                fields=["估值", "行业", "财务摘要", "公司资料"],
                used_for="补充标的背景 / 估值和商业模式复核",
                reliability="medium",
                notes="基础资料依赖公开接口可用性；若缺失，应在报告中降低相关解释置信度。",
            )
        )
    return records


def deep_background_records(symbol: str | None, market: str | None) -> list[SourceRecord]:
    return [
        record(
            "news",
            "新闻/公告/市场背景",
            f"{symbol or '标的'} 背景资料",
            fields=["headline", "published_at", "source", "summary"],
            used_for="波动解释 / 近期变化背景 / 需要复核的观察信号",
            reliability="low",
            notes="当前版本仅预留深度资料槽位；如未接入新闻或公告抓取，相关解释必须标注为基于数据的推断，不是事实披露。",
        )
    ]


def local_context_records(user_path: Path, reports_path: Path, db_path: Path) -> list[SourceRecord]:
    records: list[SourceRecord] = []
    for filename, builder in [
        ("holdings.json", holdings_source_record),
        ("analysis_history.json", history_source_record),
    ]:
        path = user_path / filename
        if path.exists():
            records.append(builder(path))
        else:
            records.append(record("local_file", "用户空间", filename, used_for="本地资料补充", reliability="low", notes="未获取到：文件不存在。"))
    if db_path.exists():
        records.append(sqlite_source_record(db_path))
    else:
        records.append(record("sqlite", "SQLite 本地数据库", db_path.name, used_for="结构化资料", reliability="low", notes="未获取到：数据库不存在。"))
    latest_reports = sorted(reports_path.glob("research_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:3] if reports_path.exists() else []
    if latest_reports:
        records.extend(generated_report_source_record(path) for path in latest_reports)
    else:
        records.append(record("generated_report", "已生成报告", "历史报告", used_for="版本追踪", reliability="low", notes="未获取到：暂无历史报告。"))
    return records


def apply_data_breadth(
    base_records: list[SourceRecord],
    *,
    breadth: str,
    user_path: Path | None = None,
    reports_path: Path | None = None,
    db_path: Path | None = None,
    symbol: str | None = None,
    market: str | None = None,
    period: str | None = None,
    data_range: str | None = None,
    cache_dir: Path | None = None,
) -> list[SourceRecord]:
    records = list(base_records)
    standard_values = {"标准", "鏍囧噯"}
    deep_values = {"深度", "娣卞害"}
    if breadth not in (standard_values | deep_values):
        return records
    if symbol and market and cache_dir:
        records.extend(realtime_quote_records(symbol, market))
        records.extend(market_source_records(symbol, market, period or "-", cache_dir=cache_dir, data_range=data_range))
    if user_path and reports_path and db_path:
        records.extend(local_context_records(user_path, reports_path, db_path))
    if breadth in deep_values:
        records.extend(deep_background_records(symbol, market))
    return records


def source_reliability_penalty(records: list[SourceRecord | dict]) -> int:
    low = 0
    failed = 0
    for item in source_dicts(records):
        if item.get("reliability") == "low":
            low += 1
        if "未获取到" in str(item.get("notes", "")):
            failed += 1
    return min(low * 5 + failed * 5, 30)
