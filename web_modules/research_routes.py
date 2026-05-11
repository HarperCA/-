# -*- coding: utf-8 -*-
from __future__ import annotations

from flask import redirect, render_template_string, request, url_for

from core.strategy_compare import compare_strategies
from web_modules.templates import (
    BACKTEST_COMPARE_TEMPLATE,
    CLEAN_HISTORY_PAGE_TEMPLATE,
    CLEAN_STRATEGY_PAGE_TEMPLATE,
    MARKET_REPORT_PAGE_TEMPLATE,
    UI_CONCEPTS_TEMPLATE,
)


def register_research_routes(app, deps: dict) -> None:
    agent = deps["agent"]
    normalize_market = deps["normalize_market"]
    normalize_period = deps["normalize_period"]
    normalize_symbol = deps["normalize_symbol"]
    friendly_error = deps["friendly_error"]
    current_user = deps["current_user"]
    ensure_user_space = deps["ensure_user_space"]
    normalize_run_time = deps["normalize_run_time"]
    run_market_report = deps["run_market_report"]
    upsert_automation_items = deps["upsert_automation_items"]
    read_market_reports = deps["read_market_reports"]
    read_automations = deps["read_automations"]
    economic_history_events = deps["economic_history_events"]
    valuation_metrics = deps["valuation_metrics"]

    @app.route("/backtest_compare")
    def backtest_compare():
        market = normalize_market(request.args.get("market") or agent.config["market"]["default_market"])
        symbol = normalize_symbol(request.args.get("symbol") or agent.config["market"]["default_symbol"], market)
        period = normalize_period(request.args.get("period") or "max")
        rows = []
        error = None
        try:
            df = agent.data_fetcher.fetch(symbol=symbol, market=market, period=period)
            rows = compare_strategies(
                df,
                initial_cash=agent.config["backtest"]["initial_cash"],
                fund_mode=(market == "fund"),
                config=agent.config.get("strategy"),
            )
        except Exception as exc:
            error = friendly_error(exc)
        return render_template_string(
            BACKTEST_COMPARE_TEMPLATE,
            rows=rows,
            error=error,
            symbol=symbol,
            market=market,
            period=period,
        )

    @app.route("/strategy")
    def strategy():
        cfg = agent.config
        strategy_cfg = cfg.get("strategy", {})
        backtest_cfg = cfg.get("backtest", {})
        fund_cfg = cfg.get("fund", {})
        redeem = fund_cfg.get("redeem_fee_tiers", {})
        risk_defaults = {
            "max_position_pct": 0.20,
            "max_total_positions": 10,
            "min_cash_ratio": 0.10,
            "stop_loss_pct": 0.07,
            "take_profit_pct": 0.15,
            "trailing_stop_pct": 0.10,
            "max_daily_loss_pct": 0.03,
            "max_drawdown_pct": 0.15,
            "drawdown_action": "halt",
            "circuit_breaker_action": "halt",
            "max_order_price_deviation_pct": 0.05,
            "max_extreme_move_pct": 0.10,
            "max_orders_per_day": 20,
            "cooldown_minutes": 5,
        }
        config_data = {
            "fast_window": strategy_cfg.get("fast_window", 10),
            "slow_window": strategy_cfg.get("slow_window", 30),
            "rsi_period": strategy_cfg.get("rsi_period", 14),
            "rsi_overbought": strategy_cfg.get("rsi_overbought", 70),
            "rsi_oversold": strategy_cfg.get("rsi_oversold", 30),
            "initial_cash": backtest_cfg.get("initial_cash", 100000),
            "commission": backtest_cfg.get("commission", 0.0003),
            "slippage": backtest_cfg.get("slippage", 0.001),
            "subscribe_fee": fund_cfg.get("subscribe_fee", 0.001),
            "redeem_7": redeem.get(7, 0.015),
            "redeem_30": redeem.get(30, 0.0075),
            "redeem_365": redeem.get(365, 0.005),
        }
        return render_template_string(CLEAN_STRATEGY_PAGE_TEMPLATE, config=config_data, risk=risk_defaults)

    @app.route("/history")
    def economic_history():
        return render_template_string(
            CLEAN_HISTORY_PAGE_TEMPLATE,
            events=economic_history_events,
            valuation_metrics=valuation_metrics,
        )

    @app.route("/market_report", methods=["GET", "POST"])
    def market_report():
        username = current_user()
        if not username:
            return redirect(url_for("login"))
        ensure_user_space(username)
        note = None
        error = None
        if request.method == "POST":
            mode = request.form.get("mode", "")
            try:
                if mode == "market_report_run":
                    report_type = request.form.get("report_type", "daily")
                    report = run_market_report(username, report_type)
                    note = f"{report['title']}已生成。"
                elif mode == "market_report_schedule":
                    run_time = normalize_run_time(request.form.get("market_report_time", "16:30"), default="16:30")
                    upsert_automation_items(username, [
                        {"id": "market_daily_report", "job_type": "market_daily_report", "run_time": run_time, "enabled": request.form.get("market_daily_enabled") == "on"},
                        {"id": "market_weekly_report", "job_type": "market_weekly_report", "run_time": run_time, "enabled": request.form.get("market_weekly_enabled") == "on"},
                    ])
                    note = "市场报告计划已保存。"
            except Exception as exc:
                app.logger.exception("market report request failed")
                error = friendly_error(exc)
        reports = read_market_reports(username=username, limit=20)
        return render_template_string(
            MARKET_REPORT_PAGE_TEMPLATE,
            reports=reports,
            latest=reports[0] if reports else None,
            automations=read_automations(username=username),
            note=note,
            error=error,
        )

    @app.route("/ui_concepts")
    def ui_concepts():
        return render_template_string(UI_CONCEPTS_TEMPLATE)
