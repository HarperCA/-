from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd


INDEX_SYMBOLS = {
    "000001": "上证指数",
    "399001": "深证成指",
    "399006": "创业板指",
    "000300": "沪深300",
    "000016": "上证50",
    "000905": "中证500",
}


@dataclass
class MarketReportGenerator:
    """Generate A-share market daily/weekly reports with defensive data fallbacks."""

    ak: Any | None = None

    def __post_init__(self) -> None:
        if self.ak is None:
            try:
                import akshare as ak

                self.ak = ak
            except Exception:
                self.ak = None

    def generate(self, report_type: str = "daily") -> dict:
        report_type = "weekly" if report_type == "weekly" else "daily"
        lookback_days = 14 if report_type == "weekly" else 7
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y%m%d")
        end_date = datetime.now().strftime("%Y%m%d")

        index_rows = self._index_performance(start_date, end_date, report_type)
        sector_rows = self._sector_performance()
        flow_rows = self._fund_flow()
        breadth = self._market_breadth()
        volatility = self._volatility_summary(index_rows)
        environment = self._judge_environment(index_rows, sector_rows, breadth, volatility)

        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        return {
            "id": f"market_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type": report_type,
            "title": "市场日报" if report_type == "daily" else "市场周报",
            "generated_at": generated_at,
            "index_performance": index_rows,
            "sector_performance": sector_rows,
            "fund_flow": flow_rows,
            "breadth": breadth,
            "volatility": volatility,
            "environment": environment,
            "text": self._format_text(
                report_type,
                generated_at,
                index_rows,
                sector_rows,
                flow_rows,
                breadth,
                volatility,
                environment,
            ),
        }

    def _index_performance(self, start_date: str, end_date: str, report_type: str) -> list[dict]:
        if self.ak is None:
            return []
        rows = []
        for symbol, name in INDEX_SYMBOLS.items():
            try:
                df = self.ak.index_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date)
                df = self._normalize_price_frame(df)
                if df.empty:
                    continue
                latest = df.iloc[-1]
                previous = df.iloc[-2] if report_type == "daily" and len(df) > 1 else df.iloc[0]
                change_pct = (float(latest["close"]) / float(previous["close"]) - 1) * 100
                rows.append({
                    "symbol": symbol,
                    "name": name,
                    "close": round(float(latest["close"]), 2),
                    "change_pct": round(change_pct, 2),
                    "volume": round(float(latest.get("volume", 0) or 0), 2),
                    "volatility_pct": round(float(df["close"].pct_change().dropna().std() * 100), 2) if len(df) > 2 else 0.0,
                })
            except Exception:
                continue
        return rows

    def _sector_performance(self) -> list[dict]:
        if self.ak is None:
            return []
        try:
            df = self.ak.stock_board_industry_name_em()
            if df is None or df.empty:
                return []
            name_col = self._find_column(df, ("板块名称", "名称", "行业")) or self._column_at(df, 1, 0)
            pct_col = self._find_column(df, ("涨跌幅", "涨跌幅%", "涨幅")) or self._first_numeric_column(df, skip={name_col})
            flow_col = self._find_column(df, ("主力净流入", "净流入", "资金净流入"))
            if not name_col or not pct_col:
                return []
            clean = pd.DataFrame({
                "name": df[name_col].astype(str),
                "change_pct": pd.to_numeric(df[pct_col], errors="coerce"),
                "main_net_inflow": pd.to_numeric(df[flow_col], errors="coerce") if flow_col else np.nan,
            }).dropna(subset=["change_pct"])
            top = clean.sort_values("change_pct", ascending=False).head(5)
            bottom = clean.sort_values("change_pct", ascending=True).head(5)
            rows = []
            for label, subset in (("strong", top), ("weak", bottom)):
                for _, row in subset.iterrows():
                    rows.append({
                        "group": label,
                        "name": row["name"],
                        "change_pct": round(float(row["change_pct"]), 2),
                        "main_net_inflow": self._round_optional(row.get("main_net_inflow")),
                    })
            return rows
        except Exception:
            return []

    def _fund_flow(self) -> list[dict]:
        if self.ak is None:
            return []
        try:
            df = self.ak.stock_sector_fund_flow_rank(indicator="今日")
            if df is None or df.empty:
                return []
            name_col = self._find_column(df, ("名称", "行业", "板块名称")) or self._column_at(df, 1, 0)
            flow_col = self._find_column(df, ("今日主力净流入-净额", "主力净流入", "净流入")) or self._first_numeric_column(df, skip={name_col})
            pct_col = self._find_column(df, ("今日涨跌幅", "涨跌幅"))
            if not name_col or not flow_col:
                return []
            clean = pd.DataFrame({
                "name": df[name_col].astype(str),
                "net_inflow": pd.to_numeric(df[flow_col], errors="coerce"),
                "change_pct": pd.to_numeric(df[pct_col], errors="coerce") if pct_col else np.nan,
            }).dropna(subset=["net_inflow"])
            rows = []
            for _, row in clean.sort_values("net_inflow", ascending=False).head(8).iterrows():
                rows.append({
                    "name": row["name"],
                    "net_inflow": round(float(row["net_inflow"]), 2),
                    "change_pct": self._round_optional(row.get("change_pct")),
                })
            return rows
        except Exception:
            return []

    def _market_breadth(self) -> dict:
        if self.ak is None:
            return {"status": "unavailable"}
        try:
            df = self.ak.stock_zh_a_spot_em()
            pct_col = self._find_column(df, ("涨跌幅", "涨跌幅%")) or self._first_numeric_column(df)
            if not pct_col:
                return {"status": "unavailable"}
            pct = pd.to_numeric(df[pct_col], errors="coerce").dropna()
            total = int(len(pct))
            if total == 0:
                return {"status": "unavailable"}
            up = int((pct > 0).sum())
            down = int((pct < 0).sum())
            flat = total - up - down
            limit_up = int((pct >= 9.8).sum())
            limit_down = int((pct <= -9.8).sum())
            return {
                "status": "ok",
                "total": total,
                "up": up,
                "down": down,
                "flat": flat,
                "up_ratio": round(up / total * 100, 2),
                "down_ratio": round(down / total * 100, 2),
                "limit_up": limit_up,
                "limit_down": limit_down,
            }
        except Exception:
            return {"status": "unavailable"}

    def _volatility_summary(self, index_rows: list[dict]) -> dict:
        vols = [row.get("volatility_pct") for row in index_rows if row.get("volatility_pct") is not None]
        if not vols:
            return {"status": "unavailable"}
        avg_vol = float(np.nanmean(vols))
        if avg_vol >= 2.5:
            label = "高波动"
        elif avg_vol >= 1.4:
            label = "中等波动"
        else:
            label = "低波动"
        return {"status": "ok", "avg_volatility_pct": round(avg_vol, 2), "label": label}

    def _judge_environment(
        self,
        index_rows: list[dict],
        sector_rows: list[dict],
        breadth: dict,
        volatility: dict,
    ) -> dict:
        avg_index_return = float(np.nanmean([row["change_pct"] for row in index_rows])) if index_rows else 0.0
        up_ratio = float(breadth.get("up_ratio", 50)) if breadth.get("status") == "ok" else 50.0
        avg_vol = float(volatility.get("avg_volatility_pct", 1.5)) if volatility.get("status") == "ok" else 1.5
        strong_sectors = [row["name"] for row in sector_rows if row.get("group") == "strong"][:3]
        weak_sectors = [row["name"] for row in sector_rows if row.get("group") == "weak"][:3]

        score = 0
        score += 1 if avg_index_return > 0.4 else (-1 if avg_index_return < -0.4 else 0)
        score += 1 if up_ratio >= 55 else (-1 if up_ratio <= 40 else 0)
        score += 1 if avg_vol < 1.4 else (-1 if avg_vol >= 2.5 else 0)

        if score >= 2:
            label = "偏多环境"
            advice = "指数和赚钱效应较好，可适度提高进攻性，但仍按风控控制单票仓位。"
        elif score <= -2:
            label = "防御环境"
            advice = "指数、涨跌分布或波动率偏弱，建议降低仓位、减少追涨，优先观察止损和现金比例。"
        else:
            label = "震荡环境"
            advice = "市场方向不够一致，适合轻仓轮动、等待放量突破或回调确认。"

        return {
            "label": label,
            "score": score,
            "avg_index_return": round(avg_index_return, 2),
            "up_ratio": round(up_ratio, 2),
            "avg_volatility_pct": round(avg_vol, 2),
            "strong_sectors": strong_sectors,
            "weak_sectors": weak_sectors,
            "advice": advice,
        }

    def _format_text(
        self,
        report_type: str,
        generated_at: str,
        index_rows: list[dict],
        sector_rows: list[dict],
        flow_rows: list[dict],
        breadth: dict,
        volatility: dict,
        environment: dict,
    ) -> str:
        title = "市场日报" if report_type == "daily" else "市场周报"
        lines = [f"{title}｜{generated_at}", "", f"市场环境：{environment['label']}（评分 {environment['score']}）", environment["advice"], ""]
        lines.append("一、指数表现")
        if index_rows:
            for row in index_rows:
                lines.append(f"- {row['name']}：{row['close']:.2f}，涨跌幅 {row['change_pct']:+.2f}%，波动率 {row['volatility_pct']:.2f}%")
        else:
            lines.append("- 指数数据暂不可用。")
        lines.append("")

        lines.append("二、板块表现")
        strong = [row for row in sector_rows if row.get("group") == "strong"][:5]
        weak = [row for row in sector_rows if row.get("group") == "weak"][:5]
        lines.append("强势板块：" + ("、".join(f"{row['name']}({row['change_pct']:+.2f}%)" for row in strong) if strong else "暂不可用"))
        lines.append("弱势板块：" + ("、".join(f"{row['name']}({row['change_pct']:+.2f}%)" for row in weak) if weak else "暂不可用"))
        lines.append("")

        lines.append("三、资金流向")
        if flow_rows:
            for row in flow_rows[:5]:
                lines.append(f"- {row['name']}：主力净流入 {row['net_inflow']:.2f}，涨跌幅 {row.get('change_pct') if row.get('change_pct') is not None else '-'}")
        else:
            lines.append("- 资金流向数据暂不可用。")
        lines.append("")

        lines.append("四、波动率与涨跌分布")
        if volatility.get("status") == "ok":
            lines.append(f"- 平均波动率：{volatility['avg_volatility_pct']:.2f}%（{volatility['label']}）")
        else:
            lines.append("- 波动率数据暂不可用。")
        if breadth.get("status") == "ok":
            lines.append(f"- 上涨 {breadth['up']} 家，下跌 {breadth['down']} 家，平盘 {breadth['flat']} 家，上涨占比 {breadth['up_ratio']:.2f}%")
            lines.append(f"- 涨停 {breadth['limit_up']} 家，跌停 {breadth['limit_down']} 家")
        else:
            lines.append("- 涨跌分布数据暂不可用。")
        return "\n".join(lines)

    @staticmethod
    def _normalize_price_frame(df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()
        rename_map = {
            "日期": "date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
        }
        out = df.rename(columns=rename_map).copy()
        if "close" not in out.columns and len(out.columns) >= 6:
            if len(out.columns) >= 10:
                fallback = {
                    out.columns[0]: "date",
                    out.columns[1]: "open",
                    out.columns[2]: "close",
                    out.columns[3]: "high",
                    out.columns[4]: "low",
                    out.columns[5]: "volume",
                }
            else:
                fallback = {
                    out.columns[0]: "date",
                    out.columns[1]: "open",
                    out.columns[2]: "high",
                    out.columns[3]: "low",
                    out.columns[4]: "close",
                    out.columns[5]: "volume",
                }
            out = out.rename(columns=fallback)
        if "date" in out.columns:
            out["date"] = pd.to_datetime(out["date"], errors="coerce")
            out = out.dropna(subset=["date"]).set_index("date")
        for col in ("open", "high", "low", "close", "volume"):
            if col in out.columns:
                out[col] = pd.to_numeric(out[col], errors="coerce")
        return out.dropna(subset=["close"]).sort_index()

    @staticmethod
    def _find_column(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
        for candidate in candidates:
            if candidate in df.columns:
                return candidate
        for column in df.columns:
            text = str(column)
            if any(candidate in text for candidate in candidates):
                return column
        return None

    @staticmethod
    def _column_at(df: pd.DataFrame, *indexes: int) -> str | None:
        for index in indexes:
            if 0 <= index < len(df.columns):
                return df.columns[index]
        return None

    @staticmethod
    def _first_numeric_column(df: pd.DataFrame, skip: set[str | None] | None = None) -> str | None:
        skip = skip or set()
        for column in df.columns:
            if column in skip:
                continue
            values = pd.to_numeric(df[column], errors="coerce")
            if values.notna().sum() > 0:
                return column
        return None

    @staticmethod
    def _round_optional(value) -> float | None:
        try:
            if pd.isna(value):
                return None
            return round(float(value), 2)
        except Exception:
            return None
