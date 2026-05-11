#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Refresh cached market data with the maximum available history."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.data_fetcher import DataFetcher


@dataclass(frozen=True)
class Target:
    market: str
    symbol: str


def _parse_cache_name(path: Path) -> Target | None:
    match = re.match(r"^(?P<market>.+)_(?P<symbol>.+)_(?P<period>1mo|3mo|6mo|1y|2y|3y|5y|10y|20y|50y|max)_1d\.csv$", path.name)
    if not match:
        return None
    symbol = match.group("symbol").replace("_", "-")
    market = match.group("market")
    if market in {"a_stock", "fund"}:
        symbol = symbol.zfill(6)
    return Target(market=market, symbol=symbol)


def discover_targets(paths: list[Path]) -> list[Target]:
    targets = set()
    for directory in paths:
        if not directory.exists():
            continue
        for path in directory.glob("*.csv"):
            target = _parse_cache_name(path)
            if target:
                targets.add(target)
    return sorted(targets, key=lambda item: (item.market, item.symbol))


def _clean_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df[["open", "high", "low", "close", "volume"]].copy()
    out.index.name = "date"
    out = out.reset_index()
    out["return_1d"] = out["close"].pct_change()
    out["range_pct"] = (out["high"] - out["low"]) / out["close"]
    out["volume_change"] = out["volume"].pct_change().replace([float("inf"), -float("inf")], pd.NA)
    return out


def refresh_target(fetcher: DataFetcher, target: Target, cleaned_dir: Path) -> tuple[Target, int, str, str]:
    df = fetcher.fetch(
        target.symbol,
        market=target.market,
        period="max",
        interval="1d",
        force_refresh=True,
    )
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    safe_symbol = "".join(ch if ch.isalnum() else "_" for ch in target.symbol.upper())
    out_path = cleaned_dir / f"{target.market}_{safe_symbol}_max_1d.csv"
    _clean_frame(df).to_csv(out_path, index=False, encoding="utf-8-sig")
    return target, len(df), df.index.min().strftime("%Y-%m-%d"), df.index.max().strftime("%Y-%m-%d")


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh existing symbols with maximum available OHLCV history.")
    parser.add_argument("--symbol", action="append", help="Symbol to refresh. May be repeated.")
    parser.add_argument("--market", default="fund", help="Market for --symbol: fund/a_stock/us_stock/crypto.")
    parser.add_argument("--cleaned-dir", default=str(ROOT / "data" / "cleaned"))
    args = parser.parse_args()

    if args.symbol:
        targets = [Target(market=args.market, symbol=symbol) for symbol in args.symbol]
    else:
        targets = discover_targets([ROOT / "data" / "cache", ROOT / "data" / "cleaned"])

    if not targets:
        print("No targets found. Use --symbol 002982 --market fund.")
        return

    fetcher = DataFetcher()
    cleaned_dir = Path(args.cleaned_dir)
    failures = []
    for target in targets:
        try:
            _, rows, start, end = refresh_target(fetcher, target, cleaned_dir)
            print(f"{target.market} {target.symbol}: {rows} rows, {start} -> {end}")
        except Exception as exc:
            failures.append((target, exc))
            print(f"FAILED {target.market} {target.symbol}: {exc}")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
