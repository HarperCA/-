# -*- coding: utf-8 -*-
from __future__ import annotations

import html
import json
import math
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd


STANDARD_SECTIONS = [
    "一句话结论",
    "数据可信度",
    "关键发现",
    "过去表现",
    "近期变化",
    "回撤与风险",
    "可能原因解释",
    "小资金用户注意事项",
    "落地结论",
    "执行清单",
    "资料来源与引用",
    "建议追问",
    "免责声明",
]

DATE_FIELDS = {"date", "日期", "time", "datetime", "交易日期", "净值日期"}
NAV_FIELDS = {"nav", "净值", "单位净值", "equity", "portfolio_value", "value"}
PRICE_FIELDS = {"close", "收盘", "收盘价", "price", "价格"}
RETURN_FIELDS = {"return", "收益率", "ret", "pct_change", "daily_return"}
SYMBOL_FIELDS = {"symbol", "代码", "ticker", "证券代码", "基金代码"}
NAME_FIELDS = {"name", "名称", "证券名称", "基金名称"}
QUANTITY_FIELDS = {"quantity", "数量", "持仓数量", "shares"}
WEIGHT_FIELDS = {"weight", "权重", "仓位", "position_weight"}
COST_FIELDS = {"avg_cost", "cost", "成本", "持仓成本", "成本价"}
PNL_FIELDS = {"pnl", "盈亏", "profit", "收益金额"}


def _source_record_dict(source: Any) -> dict:
    if isinstance(source, dict):
        return source
    to_dict = getattr(source, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    return {}


def _source_record_dicts(source_records: list | None) -> list[dict]:
    return [_source_record_dict(item) for item in (source_records or [])]


def read_uploaded_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError("仅支持 CSV / Excel 文件")


def _match_column(columns: list[str], candidates: set[str]) -> str | None:
    lowered = {str(col).strip().lower(): col for col in columns}
    for candidate in candidates:
        found = lowered.get(candidate.lower())
        if found is not None:
            return found
    return None


def normalize_uploaded_table(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    columns = list(normalized.columns)
    mapping_sets = {
        "date": DATE_FIELDS,
        "nav": NAV_FIELDS,
        "close": PRICE_FIELDS,
        "return": RETURN_FIELDS,
        "symbol": SYMBOL_FIELDS,
        "name": NAME_FIELDS,
        "quantity": QUANTITY_FIELDS,
        "weight": WEIGHT_FIELDS,
        "avg_cost": COST_FIELDS,
        "pnl": PNL_FIELDS,
    }
    rename_map: dict[str, str] = {}
    for target, candidates in mapping_sets.items():
        source = _match_column(columns, candidates)
        if source is not None and source not in rename_map:
            rename_map[source] = target
    normalized = normalized.rename(columns=rename_map)
    if "date" in normalized:
        normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce")
    for column in ["nav", "close", "return", "quantity", "weight", "avg_cost", "pnl"]:
        if column in normalized:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    return normalized


def infer_data_type(df: pd.DataFrame) -> str:
    columns = set(df.columns)
    if {"nav", "close", "return"} & columns:
        return "净值/收益曲线"
    if "symbol" in columns and ({"quantity", "weight"} & columns):
        return "持仓表"
    if "pnl" in columns:
        return "交易记录"
    return "通用表格"


def _clean_number(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
        return numeric if math.isfinite(numeric) else default
    except Exception:
        return default


def _pct(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "暂无"
    return f"{value * 100:.2f}%"


def _fmt(value: float | None, digits: int = 2) -> str:
    if value is None or not math.isfinite(value):
        return "暂无"
    return f"{value:.{digits}f}"


def _max_drawdown(returns: pd.Series) -> float:
    if returns.empty:
        return 0.0
    curve = (1 + returns.fillna(0)).cumprod()
    peak = curve.cummax()
    dd = curve / peak - 1
    return float(dd.min())


def _annual_factor_from_dates(df: pd.DataFrame) -> int:
    if "date" not in df:
        return 252
    dates = df["date"].dropna().sort_values()
    if len(dates) < 3:
        return 252
    median_days = dates.diff().dt.days.dropna().median()
    if median_days and median_days >= 20:
        return 12
    if median_days and median_days >= 5:
        return 52
    return 252


def _return_series(df: pd.DataFrame) -> pd.Series:
    if "return" in df and df["return"].notna().sum() >= 2:
        returns = df["return"].dropna().astype(float)
        if returns.abs().median() > 1:
            returns = returns / 100
        return returns
    value_col = "nav" if "nav" in df else "close" if "close" in df else None
    if value_col and df[value_col].notna().sum() >= 3:
        values = df[value_col].dropna().astype(float)
        return values.pct_change().dropna()
    return pd.Series(dtype=float)


def base_data_metrics(df: pd.DataFrame, filename: str | None = None) -> dict:
    duplicate_dates = int(df["date"].duplicated().sum()) if "date" in df else 0
    missing_ratio = float(df.isna().sum().sum() / max(df.shape[0] * max(df.shape[1], 1), 1))
    quality_score = max(0, min(100, round(100 - missing_ratio * 45 - duplicate_dates * 3)))
    market_time = "未识别"
    if "date" in df and df["date"].notna().any():
        latest_date = df["date"].dropna().max()
        if hasattr(latest_date, "strftime"):
            market_time = latest_date.strftime("%Y-%m-%d")
        else:
            market_time = str(latest_date)
    return {
        "filename": filename or "上传数据",
        "rows": int(len(df)),
        "columns": list(map(str, df.columns)),
        "market_time": market_time,
        "missing_ratio": missing_ratio,
        "duplicate_dates": duplicate_dates,
        "quality_score": quality_score,
        "sample_enough": len(df) >= 30,
    }


def return_series_metrics(df: pd.DataFrame) -> dict:
    returns = _return_series(df)
    if returns.empty:
        return {"has_return_series": False}
    factor = _annual_factor_from_dates(df)
    total_return = float((1 + returns).prod() - 1)
    mean = float(returns.mean())
    volatility = float(returns.std(ddof=0) * math.sqrt(factor)) if len(returns) > 1 else 0.0
    sharpe = float(mean * factor / volatility) if volatility else 0.0
    recent20 = float((1 + returns.tail(20)).prod() - 1) if len(returns) >= 20 else float((1 + returns).prod() - 1)
    recent60 = float((1 + returns.tail(60)).prod() - 1) if len(returns) >= 60 else recent20
    first60 = float((1 + returns.head(min(60, len(returns)))).prod() - 1)
    trend = "转强" if recent20 > first60 else "转弱" if recent20 < first60 else "变化不明显"
    return {
        "has_return_series": True,
        "periods": int(len(returns)),
        "total_return": total_return,
        "annual_return": float((1 + total_return) ** (factor / max(len(returns), 1)) - 1),
        "volatility": volatility,
        "max_drawdown": _max_drawdown(returns),
        "sharpe": sharpe,
        "recent20": recent20,
        "recent60": recent60,
        "worst_period": float(returns.min()),
        "best_period": float(returns.max()),
        "positive_ratio": float((returns > 0).mean()),
        "trend_state": trend,
    }


def portfolio_snapshot_metrics(df: pd.DataFrame) -> dict:
    metrics: dict[str, Any] = {}
    if "weight" in df and df["weight"].notna().any():
        weights = df["weight"].dropna().astype(float)
        if weights.abs().max() > 1.5:
            weights = weights / 100
        metrics["top_weight"] = float(weights.max()) if not weights.empty else None
        metrics["top3_weight"] = float(weights.sort_values(ascending=False).head(3).sum()) if not weights.empty else None
        metrics["concentration_note"] = "集中度偏高" if metrics.get("top_weight", 0) >= 0.4 else "集中度暂未明显偏高"
    elif {"quantity", "avg_cost"} <= set(df.columns):
        value = (df["quantity"].fillna(0) * df["avg_cost"].fillna(0)).astype(float)
        total = float(value.sum())
        weights = value / total if total else value
        metrics["top_weight"] = float(weights.max()) if total else None
        metrics["top3_weight"] = float(weights.sort_values(ascending=False).head(3).sum()) if total else None
        metrics["concentration_note"] = "由数量和成本估算集中度"
    metrics["holding_count"] = int(df["symbol"].nunique()) if "symbol" in df else int(len(df))
    return metrics


def trade_record_metrics(df: pd.DataFrame) -> dict:
    if "pnl" not in df:
        return {}
    pnl = df["pnl"].dropna().astype(float)
    if pnl.empty:
        return {}
    return {
        "trade_count": int(len(pnl)),
        "win_rate": float((pnl > 0).mean()),
        "total_pnl": float(pnl.sum()),
        "avg_pnl": float(pnl.mean()),
        "worst_trade": float(pnl.min()),
        "loss_count": int((pnl < 0).sum()),
    }


def metrics_from_frame(df: pd.DataFrame, filename: str | None = None) -> dict:
    normalized = normalize_uploaded_table(df)
    data_type = infer_data_type(normalized)
    metrics = base_data_metrics(normalized, filename)
    metrics["data_type"] = data_type
    metrics.update(return_series_metrics(normalized))
    if data_type == "持仓表":
        metrics.update(portfolio_snapshot_metrics(normalized))
    if data_type == "交易记录":
        metrics.update(trade_record_metrics(normalized))
    return metrics


def _option(options: dict | None, key: str, default: str) -> str:
    if not options:
        return default
    value = (options.get(key) or "").strip()
    return value or default


def landing_status(metrics: dict, options: dict | None = None) -> str:
    if not metrics.get("has_return_series") and metrics.get("data_type") != "交易记录":
        return "当前数据不足，只能作为数据验收"
    if metrics.get("max_drawdown", 0) <= -0.2:
        return "当前风险偏高，需要先做回撤复盘"
    if metrics.get("quality_score", 0) < 65 or not metrics.get("sample_enough"):
        return "可以继续观察"
    if metrics.get("sharpe", 0) < 0 or metrics.get("recent20", 0) < -0.05:
        return "暂不建议进入模拟盘"
    return "可以进入下一轮验证"


def one_sentence_conclusion(metrics: dict, options: dict | None = None) -> list[str]:
    status = landing_status(metrics, options)
    objective = _option(options, "objective", "看清过去表现、主要风险和下一步复核动作")
    return [
        f"本次报告用于{objective}；基于当前数据，结论状态为：**{status}**。",
        "这不是交易指令，而是帮助个人投资者和小资金账户做复盘、风险检查和资料补齐的工作底稿。",
    ]


def data_quality_lines(metrics: dict, options: dict | None = None) -> list[str]:
    suitability = "适合做收益/风险初步判断" if metrics.get("has_return_series") else "暂不适合做收益/风险判断"
    return [
        f"- 数据质量评分：{metrics.get('quality_score', 0)}/100。",
        f"- 缺失值比例：{_pct(metrics.get('missing_ratio', 0))}。",
        f"- 重复日期数量：{metrics.get('duplicate_dates', 0)}。",
        f"- 样本数量：{metrics.get('rows', 0)} 行，{'样本基本够用' if metrics.get('sample_enough') else '样本偏少，需要补更多历史数据'}。",
        f"- 判断范围：{suitability}；当前数据类型识别为 **{metrics.get('data_type')}**。",
    ]


def key_findings(metrics: dict, options: dict | None = None) -> list[str]:
    if metrics.get("has_return_series"):
        return [
            f"- 长期累计收益为 {_pct(metrics.get('total_return'))}，说明过去整体表现{'为正' if metrics.get('total_return', 0) >= 0 else '为负'}。",
            f"- 近 20 期收益为 {_pct(metrics.get('recent20'))}，近 60 期收益为 {_pct(metrics.get('recent60'))}，近期状态判断为 **{metrics.get('trend_state')}**。",
            f"- 最大回撤为 {_pct(metrics.get('max_drawdown'))}，这是小资金用户最需要先确认能否承受的风险指标。",
            f"- 夏普值为 {_fmt(metrics.get('sharpe'))}。它可以粗略理解为“承担波动后赚得是否顺”，数值低说明收益质量需要继续验证。",
        ]
    if metrics.get("data_type") == "持仓表":
        return [
            "- 当前数据更像持仓表，能够做集中度和结构诊断，但缺少净值/收益率时不能判断过去收益质量。",
            f"- 持仓数量约 {metrics.get('holding_count', 0)} 个，{metrics.get('concentration_note', '需要补充权重后判断集中度')}。",
            f"- 第一大权重约 {_pct(metrics.get('top_weight'))}，前三大权重约 {_pct(metrics.get('top3_weight'))}，需要检查是否过度集中。",
        ]
    if metrics.get("data_type") == "交易记录":
        return [
            f"- 当前数据更像交易记录，共识别 {metrics.get('trade_count', 0)} 条盈亏记录。",
            f"- 胜率约 {_pct(metrics.get('win_rate'))}，最差单笔盈亏为 {_fmt(metrics.get('worst_trade'))}，适合复盘亏损来源和纪律问题。",
        ]
    return ["- 当前数据字段较通用，优先用于数据质量验收和补数建议，还不能直接形成完整投资复盘。"]


def past_performance_lines(metrics: dict, options: dict | None = None) -> list[str]:
    if not metrics.get("has_return_series"):
        return ["- 未识别到净值、价格或收益率序列，过去表现暂不能计算。建议补充 date + nav/close/return。"]
    return [
        f"- 累计收益：{_pct(metrics.get('total_return'))}。",
        f"- 年化收益估算：{_pct(metrics.get('annual_return'))}。",
        f"- 正收益期占比：{_pct(metrics.get('positive_ratio'))}。这个指标可以理解为“上涨期出现的频率”，不能单独代表策略好坏。",
    ]


def recent_change_lines(metrics: dict, options: dict | None = None) -> list[str]:
    if not metrics.get("has_return_series"):
        return ["- 缺少连续净值/收益率，无法判断最近是在变好还是变差。"]
    return [
        f"- 近 20 期表现：{_pct(metrics.get('recent20'))}。",
        f"- 近 60 期表现：{_pct(metrics.get('recent60'))}。",
        f"- 状态解释：{metrics.get('trend_state')}。你需要关注这种变化是否来自市场环境、持仓集中度、交易成本或单一标的拖累。",
    ]


def drawdown_risk_lines(metrics: dict, options: dict | None = None) -> list[str]:
    if not metrics.get("has_return_series"):
        return [
            "- 当前没有收益曲线，最大回撤和波动率不能可靠计算。",
            "- 如果这是持仓表，应先补充组合净值、每日收益率或至少月度净值，再评估继续下跌时的承受能力。",
        ]
    return [
        f"- 年化波动率估算：{_pct(metrics.get('volatility'))}。波动越高，小资金用户越容易在短期亏损中被迫改变计划。",
        f"- 最大回撤：{_pct(metrics.get('max_drawdown'))}。回撤较深可能意味着它对单边下跌、流动性收缩或风格反转比较敏感。",
        f"- 最差单期收益：{_pct(metrics.get('worst_period'))}。可以把它作为设置预警线和复核仓位承受能力的参考。",
    ]


def reason_lines(metrics: dict, options: dict | None = None) -> list[str]:
    if metrics.get("data_type") == "持仓表":
        return [
            "- 可能的风险来源首先看集中度：单一标的或前三大权重过高时，小资金账户会更容易被个别波动影响。",
            "- 还需要补充行业、风格、基金类型或资产类别，才能解释组合为什么涨跌。",
        ]
    if metrics.get("data_type") == "交易记录":
        return [
            "- 盈亏分布可以帮助排查是否存在小赚大亏、连续亏损后加大风险暴露、交易成本侵蚀收益等问题。",
            "- 若没有交易时间和标的字段，亏损原因只能做初步归纳，不能定位到具体市场阶段。",
        ]
    if metrics.get("has_return_series"):
        return [
            "- 若近期转弱，常见原因包括市场整体下行、持仓风格切换、仓位过高、单一标的拖累或交易成本上升。",
            "- 这些只是复盘假设，需要用持仓、基准、行业和交易记录继续验证。",
        ]
    return ["- 当前资料不足以解释涨跌原因，建议先补净值、持仓、基准和交易记录。"]


def small_capital_notes(metrics: dict, options: dict | None = None) -> list[str]:
    return [
        "- 小资金用户更需要控制单次回撤，因为资金规模小、补仓空间和心理承受力通常更有限。",
        "- 不要只看收益，要同时看最大回撤、最差单期收益、集中度和交易成本。",
        "- 若继续下跌，应先复核仓位承受能力和预警线，再决定是否进入下一轮研究。",
    ]


def landing_lines(metrics: dict, options: dict | None = None) -> list[str]:
    status = landing_status(metrics, options)
    lines = [f"- 状态：**{status}**。"]
    if status == "当前数据不足，只能作为数据验收":
        lines.append("- 当前不能直接用于投资决策，只能作为字段验收、集中度初查和补数清单。")
    elif status == "当前风险偏高，需要先做回撤复盘":
        lines.append("- 先复盘最大回撤区间、继续下跌承受能力和风险预警线，再考虑是否进入下一轮验证。")
    elif status == "暂不建议进入模拟盘":
        lines.append("- 当前表现或质量不足，建议先补充样本、复核成本和做样本外测试。")
    elif status == "可以进入下一轮验证":
        lines.append("- 可以做样本外测试、参数敏感性分析和基准对比，但仍不构成直接投资建议。")
    else:
        lines.append("- 可以继续观察，建议一周后或补齐数据后重新生成报告对比。")
    return lines


def execution_checklist(metrics: dict, options: dict | None = None) -> list[str]:
    items = [
        "补充净值/收益率字段。",
        "检查最大回撤区间。",
        "检查是否过度集中。",
        "检查交易成本。",
        "设置预警线。",
        "保存本次报告版本。",
        "一周后重新生成报告对比。",
        "若继续下跌，复核仓位承受能力。",
    ]
    if metrics.get("data_type") == "持仓表":
        items.extend(["补充行业、资产类型和单项权重。", "补充组合净值或每日收益率。"])
    if metrics.get("data_type") == "交易记录":
        items.extend(["补充交易时间、标的、手续费和滑点。", "复盘连续亏损阶段是否违反纪律。"])
    return [f"- [ ] {item}" for item in items]


def evidence_lines(metrics: dict, options: dict | None = None, source_records: list | None = None) -> list[str]:
    lines = [
        f"- 上传文件：{metrics.get('filename', '上传数据')}。",
        f"- 识别字段：{', '.join(metrics.get('columns', [])) or '暂无'}。",
    ]
    normalized_sources = _source_record_dicts(source_records)
    if normalized_sources:
        for idx, source in enumerate(normalized_sources, start=1):
            title = source.get("title") or source.get("name") or source.get("filename") or "资料"
            source_name = source.get("source_name") or source.get("source_type") or "未知来源"
            used_for = source.get("used_for") or "用于报告判断"
            reliability = source.get("reliability") or "unknown"
            lines.append(f"- [{idx}] {source_name} / {title}：{used_for}；可信度：{reliability}。")
    else:
        lines.append("- 暂无外部资料引用；本报告主要依据上传表格本身生成。")
    lines.append("- 资料缺口：若要解释原因，建议补充基准、行业/资产类别、交易成本、持仓变化和市场背景。")
    return lines


def followup_lines(metrics: dict, options: dict | None = None) -> list[str]:
    return [
        "- 这份数据现在能不能支持进入下一轮验证？",
        "- 最大回撤发生时我需要重点复核哪些持仓或交易？",
        "- 如果继续下跌 5% 或 10%，我应该观察哪些预警信号？",
        "- 还缺哪些字段才能把结论做得更可靠？",
    ]


def build_standard_report(metrics: dict, options: dict | None = None, source_records: list | None = None) -> dict:
    report_type = _option(options, "report_type", "个人持仓体检报告")
    audience = _option(options, "audience", "个人投资者版")
    objective = _option(options, "objective", "看清过去表现、主要风险和下一步复核动作")
    normalized_sources = _source_record_dicts(source_records)
    system_fetch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sections = {
        "一句话结论": one_sentence_conclusion(metrics, options),
        "数据可信度": data_quality_lines(metrics, options),
        "关键发现": key_findings(metrics, options),
        "过去表现": past_performance_lines(metrics, options),
        "近期变化": recent_change_lines(metrics, options),
        "回撤与风险": drawdown_risk_lines(metrics, options),
        "可能原因解释": reason_lines(metrics, options),
        "小资金用户注意事项": small_capital_notes(metrics, options),
        "落地结论": landing_lines(metrics, options),
        "执行清单": execution_checklist(metrics, options),
        "资料来源与引用": evidence_lines(metrics, options, normalized_sources),
        "建议追问": followup_lines(metrics, options),
        "免责声明": [
            "本报告面向个人投资者、小资金用户和小型投研团队，用于投资复盘、资料整理和风险检查。",
            "本报告是投资复盘与风险报告助手，不提供交易执行指令，也不承诺收益。",
            "所有结论都应结合你的真实持仓、资金承受能力、交易成本和后续资料复核后再使用。",
        ],
    }
    return {
        "id": f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}",
        "title": f"{report_type} - {audience}",
        "created_at": system_fetch_time,
        "generated_at": system_fetch_time,
        "market_time": metrics.get("market_time", "未识别"),
        "system_fetch_time": system_fetch_time,
        "report_type": report_type,
        "audience": audience,
        "objective": objective,
        "metrics": metrics,
        "sections": sections,
        "source_records": normalized_sources,
    }


def render_markdown(report: dict) -> str:
    lines = [
        f"# {report.get('title', '投资复盘与风险报告')}",
        "",
        f"- 生成时间：{report.get('created_at', '')}",
        f"- 行情时间：{report.get('market_time', '未识别')}",
        f"- 系统获取时间：{report.get('system_fetch_time', report.get('created_at', ''))}",
        f"- 报告用途：{report.get('report_type', '')}",
        f"- 读者版本：{report.get('audience', '')}",
        f"- 本次问题：{report.get('objective', '')}",
        "",
    ]
    sections = report.get("sections", {})
    for section in STANDARD_SECTIONS:
        lines.append(f"## {section}")
        for item in sections.get(section, []):
            lines.append(str(item))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_report_from_upload(
    df: pd.DataFrame,
    filename: str = "上传数据",
    options: dict | None = None,
    source_records: list | None = None,
) -> dict:
    metrics = metrics_from_frame(df, filename)
    report = build_standard_report(metrics, options=options, source_records=source_records)
    report["markdown"] = render_markdown(report)
    return report


def build_report_from_analysis(
    analysis: dict,
    source: str = "analysis",
    options: dict | None = None,
    source_records: list | None = None,
) -> dict:
    rows = []
    history = analysis.get("history") or analysis.get("data") or []
    if isinstance(history, list):
        rows = history
    df = pd.DataFrame(rows) if rows else pd.DataFrame([analysis])
    return build_report_from_upload(df, filename=f"{source}.json", options=options, source_records=source_records)


def paragraph_xml(text: str) -> str:
    escaped = html.escape(text)
    return f"<w:p><w:r><w:t>{escaped}</w:t></w:r></w:p>"


def write_docx(markdown: str, path: Path) -> None:
    body = []
    for line in markdown.splitlines():
        if line.startswith("# "):
            body.append(paragraph_xml(line[2:]))
        elif line.startswith("## "):
            body.append(paragraph_xml(line[3:]))
        else:
            body.append(paragraph_xml(line))
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(body)}<w:sectPr><w:pgSz w:w=\"11906\" w:h=\"16838\"/>"
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>'
        "</w:sectPr></w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            "</Types>"
        ))
        docx.writestr("_rels/.rels", (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            "</Relationships>"
        ))
        docx.writestr("word/document.xml", document)


def write_pdf(markdown: str, path: Path) -> None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas
    except Exception:
        path.write_bytes(markdown.encode("utf-8"))
        return

    font_name = "Helvetica"
    font_candidates = [
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simsun.ttc"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for font_path in font_candidates:
        if font_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("ReportFont", str(font_path)))
                font_name = "ReportFont"
                break
            except Exception:
                continue

    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    x, y = 48, height - 48
    c.setFont(font_name, 10)
    for raw_line in markdown.splitlines():
        line = raw_line.replace("**", "")
        if line.startswith("# "):
            c.setFont(font_name, 16)
            line = line[2:]
        elif line.startswith("## "):
            c.setFont(font_name, 13)
            line = line[3:]
        else:
            c.setFont(font_name, 10)
        chunks = [line[i:i + 58] for i in range(0, len(line), 58)] or [""]
        for chunk in chunks:
            if y < 48:
                c.showPage()
                y = height - 48
                c.setFont(font_name, 10)
            c.drawString(x, y, chunk)
            y -= 16
    c.save()


def save_report_bundle(report: dict, reports_dir: str | Path) -> dict[str, Path]:
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_id = report.get("id") or f"research_{uuid4().hex[:8]}"
    markdown = report.get("markdown") or render_markdown(report)
    json_path = reports_dir / f"{report_id}.json"
    md_path = reports_dir / f"{report_id}.md"
    pdf_path = reports_dir / f"{report_id}.pdf"
    docx_path = reports_dir / f"{report_id}.docx"
    stored = dict(report)
    stored["markdown"] = markdown
    stored["files"] = {"markdown": md_path.name, "pdf": pdf_path.name, "docx": docx_path.name}
    json_path.write_text(json.dumps(stored, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    write_pdf(markdown, pdf_path)
    write_docx(markdown, docx_path)
    return {"json": json_path, "markdown": md_path, "pdf": pdf_path, "docx": docx_path}
