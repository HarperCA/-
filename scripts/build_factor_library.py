#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the SQLite factor library from cleaned OHLCV CSV files."""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.factor_store import (
    FactorStore,
    FactorSpec,
    build_market_factors,
    import_external_factor_frame,
    import_market_factor_frame,
    register_all_factors,
)


FILE_RE = re.compile(r"^(?P<market>.+)_(?P<symbol>[A-Za-z0-9.-]+)_(?P<period>[^_]+)_(?P<interval>[^_]+)\.csv$")


def parse_market_file(path: Path) -> tuple[str, str]:
    match = FILE_RE.match(path.name)
    if not match:
        raise ValueError(f"cannot parse market and symbol from {path.name}")
    return match.group("market"), match.group("symbol").upper()


def build_factor_library(input_dir: Path, db_path: Path) -> int:
    store = FactorStore(db_path)
    register_all_factors(store)

    total_rows = 0
    by_market: dict[str, list[pd.DataFrame]] = defaultdict(list)
    for path in sorted(input_dir.glob("*.csv")):
        market, symbol = parse_market_file(path)
        df = pd.read_csv(path, encoding="utf-8-sig")
        factors = build_market_factors(df, symbol=symbol)
        by_market[market].append(factors)
        print(f"prepared {len(factors)} daily rows from {path.name}")

    for market, frames in sorted(by_market.items()):
        started_at = datetime.now().isoformat(timespec="seconds")
        combined = pd.concat(frames, ignore_index=True)
        rows = import_market_factor_frame(store, combined, market=market)
        total_rows += rows
        store.record_import_batch(
            batch_id=f"market_ohlcv:{market}:{started_at}",
            source=str(input_dir),
            market=market,
            rows_imported=rows,
            started_at=started_at,
            status="success",
            message=f"imported {len(frames)} files",
        )
        print(f"imported {rows} factor rows for market={market}")
    return total_rows


def import_external_csv(path: Path, db_path: Path, factor_name: str, category: str, source: str, market: str) -> int:
    store = FactorStore(db_path)
    spec = FactorSpec(
        name=factor_name,
        category=category,
        description=f"External imported factor: {factor_name}",
        source=source,
    )
    started_at = datetime.now().isoformat(timespec="seconds")
    frame = pd.read_csv(path, encoding="utf-8-sig")
    rows = import_external_factor_frame(store, frame, spec, market=market)
    store.record_import_batch(
        batch_id=f"{source}:{market}:{factor_name}:{started_at}",
        source=str(path),
        market=market,
        rows_imported=rows,
        started_at=started_at,
        status="success",
    )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a SQLite factor library from cleaned market CSVs.")
    parser.add_argument("--input-dir", default="data/cleaned", help="Directory containing cleaned OHLCV CSV files.")
    parser.add_argument("--db", default="data/quant_app.sqlite", help="SQLite database path.")
    parser.add_argument("--external-csv", help="Optional external factor CSV with trade_date,symbol,factor_value.")
    parser.add_argument("--factor-name", help="Factor name for --external-csv.")
    parser.add_argument("--category", default="custom", help="Factor category for --external-csv.")
    parser.add_argument("--source", default="external_csv", help="Factor source for --external-csv.")
    parser.add_argument("--market", default="a_stock", help="Market for --external-csv.")
    args = parser.parse_args()

    if args.external_csv:
        if not args.factor_name:
            raise SystemExit("--factor-name is required with --external-csv")
        rows = import_external_csv(
            Path(args.external_csv),
            Path(args.db),
            args.factor_name,
            args.category,
            args.source,
            args.market,
        )
        print(f"external factor imported: {args.factor_name} ({rows} rows)")
    else:
        rows = build_factor_library(Path(args.input_dir), Path(args.db))
        print(f"factor library ready: {args.db} ({rows} rows)")


if __name__ == "__main__":
    main()
