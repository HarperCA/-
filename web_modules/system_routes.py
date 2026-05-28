# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

from flask import flash, redirect, send_file, send_from_directory, url_for


def register_system_routes(app, deps: dict) -> None:
    scheduler = deps["scheduler"]
    reports_dir = deps["reports_dir"]
    current_user = deps["current_user"]
    is_report_visible_to_user = deps["is_report_visible_to_user"]
    read_history = deps["read_history"]
    cache_count = deps["cache_count"]
    agent = deps["agent"]
    current_holdings_dataframe = deps["current_holdings_dataframe"]
    read_alerts = deps["read_alerts"]
    export_rows_to_files = deps["export_rows_to_files"]
    send_user_export = deps["send_user_export"]
    safe_username = deps["safe_username"]

    @app.route("/reports/<path:filename>")
    def serve_report(filename: str):
        if not is_report_visible_to_user(filename, current_user()):
            return "Not found", 404
        directory = reports_dir() if callable(reports_dir) else reports_dir
        return send_from_directory(directory, filename)

    @app.route("/health")
    def health():
        return {
            "status": "ok",
            "scheduler_running": scheduler.running,
            "job_count": len(scheduler.get_jobs()) if scheduler.running else 0,
        }

    @app.route("/status")
    def status():
        return {
            "status": "ok",
            "history_count": len(read_history(username=current_user(), limit=1000)),
            "cache_count": cache_count(),
            "scheduler_running": scheduler.running,
            "job_count": len(scheduler.get_jobs()) if scheduler.running else 0,
            "default_symbol": agent.config["market"]["default_symbol"],
            "default_market": agent.config["market"]["default_market"],
        }

    @app.route("/export/<dataset>.<fmt>")
    def export_dataset(dataset: str, fmt: str):
        username = current_user()
        if not username:
            return redirect(url_for("login"))
        if dataset == "holdings":
            rows = current_holdings_dataframe()
        elif dataset == "history":
            rows = read_history(username=username, limit=1000)
        elif dataset == "alerts":
            rows = read_alerts(username=username)
        else:
            flash("不支持导出这个数据集。")
            return redirect(url_for("index"))

        csv_path, xlsx_path, pdf_path = export_rows_to_files(rows, f"{dataset}_{safe_username(username)}", username=username)
        if fmt == "csv":
            return send_user_export(csv_path, username)
        if fmt == "xlsx":
            return send_user_export(xlsx_path, username)
        if fmt == "pdf":
            return send_user_export(pdf_path, username)
        flash("不支持这个导出格式。")
        return redirect(url_for("index"))

    @app.errorhandler(413)
    def request_too_large(_exc):
        return "请求内容太大，请缩小后再提交。", 413

    @app.errorhandler(500)
    def internal_error(exc):
        app.logger.exception("unhandled request error: %s", exc)
        return "服务临时异常，已写入日志，请稍后再试。", 500
