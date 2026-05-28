#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Clean cached OHLCV market data for quant research workflows."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = ["date", "open", "high", "low", "close", "volume"]
PRICE_COLUMNS = ["open", "high", "low", "close"]
OUTPUT_COLUMNS = REQUIRED_COLUMNS + ["return_1d", "range_pct", "volume_change"]


@dataclass
class QualityReport:
    file: str
    rows_raw: int
    rows_clean: int
    start_date: str
    end_date: str
    missing_required_values: int
    duplicate_dates_removed: int
    invalid_dates_removed: int
    invalid_price_rows_removed: int
    negative_volume_fixed: int
    ohlc_rows_repaired: int
    large_abs_return_rows: int


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="gbk")


def clean_ohlcv(path: Path) -> tuple[pd.DataFrame, QualityReport]:
    raw = _read_csv(path)
    rows_raw = len(raw)
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in raw.columns]
    if missing_columns:
        raise ValueError(f"{path.name} missing columns: {', '.join(missing_columns)}")

    df = raw[REQUIRED_COLUMNS].copy()
    missing_required_values = int(df[REQUIRED_COLUMNS].isna().sum().sum())

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    invalid_dates_removed = int(df["date"].isna().sum())
    df = df.dropna(subset=["date"])

    for col in PRICE_COLUMNS + ["volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    before_dupes = len(df)
    df = df.sort_values("date")
    df = df.drop_duplicates(subset=["date"], keep="last")
    duplicate_dates_removed = before_dupes - len(df)

    price_na = df[PRICE_COLUMNS].isna().any(axis=1)
    non_positive_price = (df[PRICE_COLUMNS] <= 0).any(axis=1)
    invalid_price_rows_removed = int((price_na | non_positive_price).sum())
    df = df.loc[~(price_na | non_positive_price)].copy()

    volume = df["volume"].fillna(0)
    negative_volume_fixed = int((volume < 0).sum())
    df["volume"] = volume.clip(lower=0)

    repaired_high = df[["open", "high", "close"]].max(axis=1)
    repaired_low = df[["open", "low", "close"]].min(axis=1)
    ohlc_rows_repaired = int(((df["high"] != repaired_high) | (df["low"] != repaired_low)).sum())
    df["high"] = repaired_high
    df["low"] = repaired_low

    df["return_1d"] = df["close"].pct_change()
    df["range_pct"] = (df["high"] - df["low"]) / df["close"]
    df["volume_change"] = df["volume"].pct_change().replace([float("inf"), -float("inf")], pd.NA)
    large_abs_return_rows = int((df["return_1d"].abs() > 0.2).sum())

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df = df[OUTPUT_COLUMNS]

    report = QualityReport(
        file=path.name,
        rows_raw=rows_raw,
        rows_clean=len(df),
        start_date=str(df["date"].iloc[0]) if not df.empty else "",
        end_date=str(df["date"].iloc[-1]) if not df.empty else "",
        missing_required_values=missing_required_values,
        duplicate_dates_removed=duplicate_dates_removed,
        invalid_dates_removed=invalid_dates_removed,
        invalid_price_rows_removed=invalid_price_rows_removed,
        negative_volume_fixed=negative_volume_fixed,
        ohlc_rows_repaired=ohlc_rows_repaired,
        large_abs_return_rows=large_abs_return_rows,
    )
    return df, report


def summarize_quality(reports: list[QualityReport]) -> dict:
    """Build a compact aggregate view for quick data-quality triage."""
    issue_fields = [
        "missing_required_values",
        "duplicate_dates_removed",
        "invalid_dates_removed",
        "invalid_price_rows_removed",
        "negative_volume_fixed",
        "ohlc_rows_repaired",
        "large_abs_return_rows",
    ]
    totals = {
        "files": len(reports),
        "rows_raw": sum(item.rows_raw for item in reports),
        "rows_clean": sum(item.rows_clean for item in reports),
    }
    totals["rows_removed"] = totals["rows_raw"] - totals["rows_clean"]
    totals.update({field: sum(getattr(item, field) for item in reports) for field in issue_fields})

    flagged_files = [
        item.file
        for item in reports
        if any(getattr(item, field) for field in issue_fields)
    ]
    return {
        **totals,
        "flagged_files": flagged_files,
        "status": "ok" if not flagged_files else "review",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean cached OHLCV CSV files.")
    parser.add_argument("--input-dir", default="data/cache", help="Directory containing raw CSV cache files.")
    parser.add_argument("--output-dir", default="data/cleaned", help="Directory for cleaned CSV files.")
    parser.add_argument("--report", default="reports/data_quality_report.json", help="JSON quality report path.")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    report_path = Path(args.report)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    reports: list[QualityReport] = []
    for path in sorted(input_dir.glob("*.csv")):
        cleaned, report = clean_ohlcv(path)
        cleaned.to_csv(output_dir / path.name, index=False, encoding="utf-8-sig")
        reports.append(report)

    report_payload = {
        "source_dir": str(input_dir),
        "output_dir": str(output_dir),
        "summary": summarize_quality(reports),
        "files": [asdict(item) for item in reports],
    }
    report_path.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"cleaned {len(reports)} files -> {output_dir}")
    print(f"quality report -> {report_path}")


if __name__ == "__main__":
    main()
