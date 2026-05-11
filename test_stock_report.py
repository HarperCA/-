#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Checks for stock financial report formatting."""

from core.value_analysis import format_value_report


def check_us_stock_report() -> None:
    report = format_value_report({
        "market": "us_stock",
        "symbol": "DEMO",
        "name": "Demo Corp",
        "sector": "Technology",
        "industry": "Software",
        "description": "Demo Corp sells subscription software and cloud services to enterprise customers.",
        "market_cap": 200_000_000_000,
        "pe_trailing": 25,
        "pb": 6,
        "ps": 8,
        "total_assets": 80_000_000_000,
        "total_liabilities": 30_000_000_000,
        "total_equity": 50_000_000_000,
        "current_ratio": 1.8,
        "debt_to_equity": 55,
        "operating_cashflow": 18_000_000_000,
        "free_cashflow": 15_000_000_000,
        "capex": -3_000_000_000,
        "revenue": 60_000_000_000,
        "gross_profit": 42_000_000_000,
        "operating_income": 20_000_000_000,
        "net_income": 16_000_000_000,
        "roe": 0.32,
        "revenue_growth": 0.18,
        "gross_margin": 0.70,
        "profit_margin": 0.26,
    })
    required = [
        "公司财务与商业模式分析",
        "营业模式",
        "现金流",
        "经营现金流",
        "自由现金流",
        "收入与盈利能力",
        "营业收入",
        "净利润",
        "财务质量检查",
        "股票收益率(E/P)",
    ]
    missing = [item for item in required if item not in report]
    assert not missing, f"Missing sections: {missing}\n{report}"


def check_a_stock_report_with_missing_cashflow() -> None:
    report = format_value_report({
        "market": "a_stock",
        "symbol": "000001",
        "name": "平安银行",
        "industry": "银行",
        "pe": "6.5",
        "pb": "0.6",
        "roe": "10.5",
        "debt_ratio": "91.2",
        "profit_margin": "30.1",
        "revenue_growth": "2.4",
    })
    required = [
        "公司财务与商业模式分析",
        "营业模式",
        "资产负债率",
        "暂无可靠现金流数据",
        "股票收益率(E/P)",
    ]
    missing = [item for item in required if item not in report]
    assert not missing, f"Missing A-share fallback sections: {missing}\n{report}"


if __name__ == "__main__":
    check_us_stock_report()
    check_a_stock_report_with_missing_cashflow()
    print("stock report checks passed")
