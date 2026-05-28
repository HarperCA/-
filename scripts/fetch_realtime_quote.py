#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch a quasi-realtime quote snapshot for report citation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.realtime_data import fetch_realtime_quote
from web_modules.source_records import realtime_quote_source_record


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch quasi-realtime quote snapshot.")
    parser.add_argument("symbol", help="Symbol, e.g. 000001, 002982, AAPL, BTC-USD.")
    parser.add_argument("--market", default="a_stock", choices=["a_stock", "fund", "us_stock", "crypto"])
    parser.add_argument("--source-record", action="store_true", help="Print report SourceRecord instead of raw quote.")
    args = parser.parse_args()

    quote = fetch_realtime_quote(args.symbol, args.market)
    payload = realtime_quote_source_record(quote).to_dict() if args.source_record else quote.to_dict()
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
