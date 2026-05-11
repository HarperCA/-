#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run a VMOM factor research pass on local OHLCV cache files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.factor_research import read_ohlcv_csv, run_vmom_parameter_grid


def main() -> None:
    parser = argparse.ArgumentParser(description="Research the volatility-adjusted momentum factor.")
    parser.add_argument("--input-dir", default="data/cache", help="Directory containing OHLCV CSV files.")
    parser.add_argument("--pattern", default="*_1y_1d.csv", help="CSV file glob pattern.")
    parser.add_argument("--output-csv", default="reports/vmom_factor_grid.csv", help="Grid result CSV path.")
    parser.add_argument("--output-json", default="reports/vmom_factor_summary.json", help="Summary JSON path.")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    paths = sorted(input_dir.glob(args.pattern))
    series_by_asset = {path.stem: read_ohlcv_csv(path) for path in paths}
    if len(series_by_asset) < 3:
        raise RuntimeError("VMOM research needs at least 3 assets for cross-sectional IC.")

    grid = run_vmom_parameter_grid(series_by_asset)
    output_csv = Path(args.output_csv)
    output_json = Path(args.output_json)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)

    grid.to_csv(output_csv, index=False, encoding="utf-8-sig")
    best = grid.iloc[0].to_dict() if not grid.empty else {}
    payload = {
        "input_dir": str(input_dir),
        "pattern": args.pattern,
        "asset_count": len(series_by_asset),
        "assets": sorted(series_by_asset),
        "best": best,
        "row_count": int(len(grid)),
    }
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"assets: {len(series_by_asset)}")
    print(f"grid rows: {len(grid)}")
    print(f"best: {best}")
    print(f"csv: {output_csv}")
    print(f"json: {output_json}")


if __name__ == "__main__":
    main()
