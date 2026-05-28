#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
AI 閲忓寲鏅鸿兘浣?- Web 鐗堝叆鍙?
杩愯鏂瑰紡:
    python web_app.py
鐒跺悗鎵撳紑:
    http://127.0.0.1:5000
"""

import io
import json
import logging
import os
import shutil
import sys
import traceback
import re
import zipfile
from datetime import datetime, timedelta
from contextlib import redirect_stdout
from logging.handlers import RotatingFileHandler
from pathlib import Path
from uuid import uuid4

from flask import Flask, render_template_string, request, url_for, session, send_file
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED
from apscheduler.schedulers.background import BackgroundScheduler

from agent.quant_agent import QuantAgent
from core.value_analysis import fetch_stock_value, format_value_report
from core.holdings_manager import HoldingsManager
from core.indicators import add_all_indicators, generate_signal_summary
from core.market_report import MarketReportGenerator
from core.storage import SQLiteDataStore
from main import parse_natural_language_command
from reports.visualizer import ReportVisualizer
from web_modules.automation import (
    bounded_int as _bounded_int,
    cleanup_old_files as _cleanup_old_files,
    normalize_run_time as _normalize_run_time,
    trim_json_list_file,
)
from web_modules.auth_routes import register_auth_routes
from web_modules.exporting import export_rows_to_files as build_export_files
from web_modules.forms import (
    normalize_market as _normalize_market,
    normalize_period as _normalize_period,
    normalize_symbol as _normalize_symbol,
    safe_export_stem,
    safe_float as _safe_float,
)
from web_modules.main_routes import register_main_routes
from web_modules.report_files import (
    is_report_visible_to_user as report_visible_to_user,
    list_recent_reports as build_recent_reports,
    report_prefix_for_user,
    to_image_url,
)
from web_modules.report_routes import register_report_routes
from web_modules.research_report import build_report_from_analysis, save_report_bundle
from web_modules.source_records import apply_data_breadth, record
from web_modules.research_routes import register_research_routes
from web_modules.system_routes import register_system_routes
from web_modules import security as security_helpers
from web_modules.security import (
    clear_login_failures as _clear_login_failures,
    hash_password as _hash_password,
    is_valid_username as _is_valid_username,
    legacy_hash_password as _legacy_hash_password,
    login_blocked_until as _login_blocked_until,
    parse_bounded_float as _parse_bounded_float,
    record_login_failure as _record_login_failure,
    safe_username as _safe_username,
    validate_buy_date as _validate_buy_date,
    validate_market as _validate_market,
    validate_period as _validate_period,
    verify_password as _verify_password,
)
from web_modules.templates import (
    PAGE_TEMPLATE,
    LOGIN_PAGE_TEMPLATE,
    REGISTER_PAGE_TEMPLATE,
    STRATEGY_PAGE_TEMPLATE,
    HISTORY_PAGE_TEMPLATE,
    BACKTEST_COMPARE_TEMPLATE,
    CLEAN_STRATEGY_PAGE_TEMPLATE,
    CLEAN_HISTORY_PAGE_TEMPLATE,
    MARKET_REPORT_PAGE_TEMPLATE,
    UI_CONCEPTS_TEMPLATE,
)
from scripts.refresh_max_history import discover_targets, refresh_target


BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
DATA_DIR = BASE_DIR / "data"
USERSPACE_DIR = DATA_DIR / "userspace"
LEGACY_HISTORY_FILE = DATA_DIR / "analysis_history.json"
LEGACY_HOLDINGS_FILE = DATA_DIR / "holdings.json"
SQLITE_FILE = DATA_DIR / "quant_app.sqlite"
SESSION_SECRET_FILE = DATA_DIR / ".session_secret"
LOGS_DIR = BASE_DIR / "logs"
LOGIN_FAILURE_LIMIT = security_helpers.LOGIN_FAILURE_LIMIT
LOGIN_FAILURE_WINDOW = security_helpers.LOGIN_FAILURE_WINDOW
LOGIN_LOCKOUT = security_helpers.LOGIN_LOCKOUT
LOGIN_FAILURES = security_helpers.LOGIN_FAILURES

app = Flask(__name__)


def _load_secret_key() -> str:
    env_secret = os.getenv("FLASK_SECRET_KEY") or os.getenv("SECRET_KEY")
    if env_secret:
        return env_secret
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if SESSION_SECRET_FILE.exists():
        try:
            secret = SESSION_SECRET_FILE.read_text(encoding="utf-8").strip()
            if secret:
                return secret
        except Exception:
            pass
    import secrets
    secret = secrets.token_hex(32)
    SESSION_SECRET_FILE.write_text(secret, encoding="utf-8")
    return secret


app.secret_key = _load_secret_key()
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,
)

LOGS_DIR.mkdir(parents=True, exist_ok=True)
file_handler = RotatingFileHandler(LOGS_DIR / "web_app.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

agent = QuantAgent(config_path=str(BASE_DIR / "config.yaml"), paper_trade=False)
visualizer = ReportVisualizer(output_dir=str(REPORTS_DIR))
market_reporter = MarketReportGenerator()
scheduler = BackgroundScheduler(
    timezone="Asia/Shanghai",
    job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 300},
)
sqlite_store = SQLiteDataStore(SQLITE_FILE)

USERS_FILE = DATA_DIR / "users.json"

def _load_users() -> dict:
    if USERS_FILE.exists():
        try:
            return json.loads(USERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_users(users: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")

def _csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = uuid4().hex + uuid4().hex
        session["csrf_token"] = token
    return token


def _csrf_input() -> str:
    return f'<input type="hidden" name="csrf_token" value="{_csrf_token()}">'


def _inject_csrf_fields(html: str) -> str:
    token_field = str(_csrf_input())
    html = re.sub(r"(<form\b[^>]*method=[\"']post[\"'][^>]*>)", r"\1" + token_field, html, flags=re.IGNORECASE)
    html = re.sub(r"(<form\b[^>]*method=post\b[^>]*>)", r"\1" + token_field, html, flags=re.IGNORECASE)
    return html


@app.context_processor
def _template_helpers() -> dict:
    return {"csrf_token": _csrf_token, "csrf_input": _csrf_input}


@app.before_request
def _protect_post_requests():
    if request.method != "POST":
        return None
    expected = session.get("csrf_token") or _csrf_token()
    supplied = request.form.get("csrf_token", "") or request.headers.get("X-CSRF-Token", "")
    if not supplied or supplied != expected:
        return "CSRF validation failed", 400
    return None


@app.after_request
def _add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    if response.content_type and response.content_type.startswith("text/html"):
        try:
            response.set_data(_inject_csrf_fields(response.get_data(as_text=True)))
        except Exception:
            pass
    return response


def _current_user() -> str | None:
    return session.get("username")


def _user_dir(username: str | None) -> Path:
    path = USERSPACE_DIR / _safe_username(username)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _user_file(username: str | None, name: str) -> Path:
    return _user_dir(username) / name


def _tag_rows_with_username(rows: list[dict], username: str | None) -> list[dict]:
    safe_username = _safe_username(username)
    tagged = []
    for row in rows or []:
        item = dict(row or {})
        item.setdefault("username", safe_username)
        tagged.append(item)
    return tagged


def _ensure_user_space(username: str | None) -> None:
    if not username:
        return
    user_dir = _user_dir(username)
    holdings_file = user_dir / "holdings.json"
    history_file = user_dir / "analysis_history.json"
    alerts_file = user_dir / "alerts.json"
    automation_file = user_dir / "automations.json"
    notifications_file = user_dir / "notifications.json"

    if not holdings_file.exists() and LEGACY_HOLDINGS_FILE.exists():
        try:
            legacy = json.loads(LEGACY_HOLDINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(legacy, list):
                holdings_file.write_text(json.dumps({_safe_username(username): _tag_rows_with_username(legacy, username)}, ensure_ascii=False, indent=2), encoding="utf-8")
            elif isinstance(legacy, dict) and legacy and all(isinstance(v, list) for v in legacy.values()):
                safe_username = _safe_username(username)
                if username in legacy:
                    holdings_file.write_text(json.dumps({safe_username: _tag_rows_with_username(legacy.get(username, []), username)}, ensure_ascii=False, indent=2), encoding="utf-8")
                elif safe_username in legacy:
                    holdings_file.write_text(json.dumps({safe_username: _tag_rows_with_username(legacy.get(safe_username, []), username)}, ensure_ascii=False, indent=2), encoding="utf-8")
                elif len(legacy) == 1:
                    only_key = next(iter(legacy))
                    holdings_file.write_text(json.dumps({safe_username: _tag_rows_with_username(legacy.get(only_key, []), username)}, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
    if not history_file.exists() and LEGACY_HISTORY_FILE.exists():
        try:
            legacy_history = json.loads(LEGACY_HISTORY_FILE.read_text(encoding="utf-8"))
            if isinstance(legacy_history, list):
                history_file.write_text(json.dumps(_tag_rows_with_username(legacy_history, username), ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
    for file_path, default_value in (
        (alerts_file, []),
        (automation_file, []),
        (notifications_file, []),
    ):
        if not file_path.exists():
            file_path.write_text(json.dumps(default_value, ensure_ascii=False, indent=2), encoding="utf-8")


def _current_holdings_mgr() -> HoldingsManager:
    username = _current_user()
    _ensure_user_space(username)
    return HoldingsManager(filepath=str(_user_file(username, "holdings.json")), username=_safe_username(username))


def _read_json_file(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def _write_json_file(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _sync_sqlite_dataset(username: str | None, dataset: str, rows: list[dict]) -> None:
    if not username:
        return
    try:
        sqlite_store.replace_dataset(_safe_username(username), dataset, rows)
    except Exception:
        pass


def _sync_sqlite_user_data(username: str | None) -> None:
    if not username:
        return
    safe_username = _safe_username(username)
    try:
        mgr = HoldingsManager(filepath=str(_user_file(username, "holdings.json")), username=safe_username)
        _sync_sqlite_dataset(username, "holdings", [h.__dict__ for h in mgr.list_all()])
        _sync_sqlite_dataset(username, "history", _read_history(username=username, limit=1000))
        _sync_sqlite_dataset(username, "alerts", _read_alerts(username=username))
        _sync_sqlite_dataset(username, "automations", _read_automations(username=username))
    except Exception:
        pass








ECONOMIC_HISTORY_EVENTS = [
    {
        "year": "1630s",
        "title": "Dutch Tulip Mania",
        "summary": "A classic early asset bubble driven by scarcity, leverage-like promises and fast sentiment reversal.",
        "tags": ["bubble", "speculation", "sentiment"],
    },
    {
        "year": "1720",
        "title": "South Sea Bubble",
        "summary": "Debt restructuring narratives and equity speculation ended in a crash that reshaped British financial regulation.",
        "tags": ["credit", "regulation", "equity"],
    },
    {
        "year": "1929-1933",
        "title": "Great Depression",
        "summary": "Equity collapse, bank failures and demand contraction pushed modern fiscal, monetary and market regulation forward.",
        "tags": ["crash", "banks", "policy"],
    },
    {
        "year": "1970s",
        "title": "Stagflation Shock",
        "summary": "Oil shocks and inflation changed the way markets priced rates, commodities and real growth risk.",
        "tags": ["inflation", "oil", "rates"],
    },
    {
        "year": "1997-1998",
        "title": "Asian Financial Crisis",
        "summary": "Currency pegs, foreign debt and liquidity stress created a regional crisis with lasting lessons for FX risk.",
        "tags": ["currency", "liquidity", "Asia"],
    },
    {
        "year": "2000-2002",
        "title": "Dot-com Bust",
        "summary": "Internet growth expectations detached from cash flow, then valuations compressed sharply after funding conditions changed.",
        "tags": ["technology", "valuation", "growth"],
    },
    {
        "year": "2008",
        "title": "Global Financial Crisis",
        "summary": "Housing leverage, securitization and banking fragility triggered a systemic crisis and a new era of central-bank intervention.",
        "tags": ["housing", "banks", "systemic risk"],
    },
    {
        "year": "2020",
        "title": "Pandemic Market Shock",
        "summary": "A sudden stop in activity caused a liquidity shock, followed by aggressive policy support and a rapid risk-asset rebound.",
        "tags": ["pandemic", "liquidity", "policy"],
    },
]


VALUATION_METRICS = [
    {"label": "市盈率", "value": "PE", "description": "用价格与盈利对比估值，适合盈利稳定的公司。"},
    {"label": "市净率", "value": "PB", "description": "用价格与净资产对比估值，常用于银行、保险和周期行业。"},
    {"label": "市销率", "value": "PS", "description": "用价格与收入对比估值，适合利润尚未稳定的成长型公司。"},
    {"label": "现金流收益率", "value": "FCF Yield", "description": "用自由现金流衡量资产产生真金白银的能力。"},
]


def _to_image_url(path_str: str | None) -> str | None:
    if not path_str:
        return None
    path = Path(path_str)
    if not path.is_absolute():
        path = (BASE_DIR / path).resolve()
    if not path.exists():
        return None
    try:
        rel_name = path.relative_to(REPORTS_DIR).as_posix()
    except ValueError:
        return None
    return url_for("serve_report", filename=rel_name)


def _report_prefix_for_user(username: str | None) -> str:
    return f"{_safe_username(username) if username else 'guest'}_"


def _is_report_visible_to_user(filename: str, username: str | None) -> bool:
    if not filename.endswith("_analysis.png"):
        return False
    if "/" in filename or "\\" in filename:
        return False
    return filename.startswith(_report_prefix_for_user(username))


def _list_recent_reports(limit: int = 8) -> list[dict]:
    items = []
    if not REPORTS_DIR.exists():
        return items
    username = _current_user()
    prefix = _report_prefix_for_user(username)
    visible_reports = [
        path
        for path in REPORTS_DIR.glob(f"{prefix}*_analysis.png")
        if _is_report_visible_to_user(path.name, username)
    ]
    for path in sorted(visible_reports, key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
        symbol = path.stem.replace("_analysis", "").replace("_", "-")
        items.append({
            "label": f"{symbol} 鍒嗘瀽鍥捐〃",
            "time": path.stat().st_mtime,
            "url": _to_image_url(str(path)),
        })
    for item in items:
        from datetime import datetime
        item["time"] = datetime.fromtimestamp(item["time"]).strftime("%Y-%m-%d %H:%M")
    return items


def _read_history(username: str | None = None, limit: int = 20) -> list[dict]:
    username = username or _current_user()
    if username:
        _ensure_user_space(username)
        history_file = _user_file(username, "analysis_history.json")
        data = _read_json_file(history_file, [])
        if isinstance(data, list):
            return data[:limit]
    items = []
    for item in _list_recent_reports(limit):
        symbol = item["label"].replace(" 鍒嗘瀽鍥捐〃", "")
        items.append({
            "time": item["time"],
            "symbol": symbol,
            "market": "",
            "period": "",
            "use_ai": False,
            "latest_price": "-",
            "analysis_image": item["url"],
        })
    return items


def _cache_count() -> int:
    cache_dir = DATA_DIR / "cache"
    return len(list(cache_dir.glob("*.csv"))) if cache_dir.exists() else 0


def _write_history_item(item: dict, username: str | None = None, limit: int = 50) -> None:
    username = username or _current_user()
    if not username:
        return
    _ensure_user_space(username)
    item = dict(item)
    item["username"] = _safe_username(username)
    history = _read_history(username=username, limit=limit)
    deduped = [
        old for old in history
        if not (
            old.get("symbol") == item.get("symbol")
            and old.get("market") == item.get("market")
            and old.get("period") == item.get("period")
            and old.get("use_ai") == item.get("use_ai")
        )
    ]
    history = [item, *deduped][:limit]
    _write_json_file(_user_file(username, "analysis_history.json"), history)
    _sync_sqlite_dataset(username, "history", history)


def _read_alerts(username: str | None = None) -> list[dict]:
    username = username or _current_user()
    if not username:
        return []
    _ensure_user_space(username)
    data = _read_json_file(_user_file(username, "alerts.json"), [])
    return data if isinstance(data, list) else []


def _write_alerts(alerts: list[dict], username: str | None = None) -> None:
    username = username or _current_user()
    if not username:
        return
    _ensure_user_space(username)
    rows = _tag_rows_with_username(alerts, username)
    _write_json_file(_user_file(username, "alerts.json"), rows)
    _sync_sqlite_dataset(username, "alerts", rows)


def _read_notifications(username: str | None = None) -> list[dict]:
    username = username or _current_user()
    if not username:
        return []
    _ensure_user_space(username)
    data = _read_json_file(_user_file(username, "notifications.json"), [])
    return data if isinstance(data, list) else []


def _write_notifications(items: list[dict], username: str | None = None) -> None:
    username = username or _current_user()
    if not username:
        return
    _ensure_user_space(username)
    _write_json_file(_user_file(username, "notifications.json"), items[:100])


def _push_notification(message: str, username: str | None = None, level: str = "info") -> None:
    username = username or _current_user()
    if not username:
        return
    items = _read_notifications(username=username)
    items.insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "level": level,
        "message": message,
    })
    _write_notifications(items, username=username)
    webhook_url = os.environ.get("ALERT_WEBHOOK_URL", "").strip()
    if webhook_url:
        try:
            import requests
            requests.post(
                webhook_url,
                json={"username": _safe_username(username), "level": level, "message": message},
                timeout=5,
            )
        except Exception:
            pass


def _consume_notifications(username: str | None = None) -> list[dict]:
    username = username or _current_user()
    if not username:
        return []
    items = _read_notifications(username=username)
    _write_notifications([], username=username)
    return items


def _read_automations(username: str | None = None) -> list[dict]:
    username = username or _current_user()
    if not username:
        return []
    _ensure_user_space(username)
    data = _read_json_file(_user_file(username, "automations.json"), [])
    return data if isinstance(data, list) else []


def _write_automations(items: list[dict], username: str | None = None) -> None:
    username = username or _current_user()
    if not username:
        return
    _ensure_user_space(username)
    rows = _tag_rows_with_username(items, username)
    _write_json_file(_user_file(username, "automations.json"), rows)
    _sync_sqlite_dataset(username, "automations", rows)


def _append_automation_log(username: str, item: dict) -> None:
    log_file = _user_file(username, "automation_log.json")
    data = _read_json_file(log_file, [])
    if not isinstance(data, list):
        data = []
    data.insert(0, item)
    _write_json_file(log_file, data[:100])
    _sync_sqlite_dataset(username, "automation_log", data[:100])


def _read_automation_log(username: str | None = None, limit: int = 20) -> list[dict]:
    username = username or _current_user()
    if not username:
        return []
    data = _read_json_file(_user_file(username, "automation_log.json"), [])
    return data[:limit] if isinstance(data, list) else []


def _read_market_reports(username: str | None = None, limit: int = 20) -> list[dict]:
    username = username or _current_user()
    if not username:
        return []
    _ensure_user_space(username)
    data = _read_json_file(_user_file(username, "market_reports.json"), [])
    return data[:limit] if isinstance(data, list) else []


def _write_market_reports(reports: list[dict], username: str | None = None) -> None:
    username = username or _current_user()
    if not username:
        return
    _ensure_user_space(username)
    rows = _tag_rows_with_username(reports[:50], username)
    _write_json_file(_user_file(username, "market_reports.json"), rows)
    _sync_sqlite_dataset(username, "market_reports", rows)


def _research_report_dir(username: str | None) -> Path:
    path = _user_dir(username) / "research_reports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _save_standard_research_report(report: dict, username: str | None = None) -> dict:
    username = username or _current_user() or "guest"
    paths = save_report_bundle(report, _research_report_dir(username))
    return {key: str(value) for key, value in paths.items()}


def _analysis_source_records(analysis_result: dict, username: str | None = None, data_breadth: str = "标准") -> list:
    username = username or _current_user() or "guest"
    base = [
        record(
            "analysis_result",
            "系统分析结果",
            f"{analysis_result.get('symbol', '-')} 分析输出",
            fields=list(analysis_result.keys()),
            used_for="收益计算 / 回撤分析 / 风险解释 / 报告生成",
            reliability="medium",
            notes="来自当前项目分析链路，包含行情计算、指标、回测曲线和图表路径。",
        )
    ]
    return apply_data_breadth(
        base,
        breadth=data_breadth,
        user_path=_user_dir(username),
        reports_path=_research_report_dir(username),
        db_path=DB_PATH,
        cache_dir=DATA_DIR / "cache",
        symbol=analysis_result.get("symbol"),
        market=analysis_result.get("market"),
        period=analysis_result.get("period"),
        data_range=analysis_result.get("data_range"),
    )


def _upsert_automation_items(username: str, new_items: list[dict]) -> list[dict]:
    ids = {item["id"] for item in new_items}
    existing = [item for item in _read_automations(username=username) if item.get("id") not in ids]
    merged = [*existing, *new_items]
    _write_automations(merged, username=username)
    _reload_user_jobs(username)
    return merged


def _run_market_report(username: str, report_type: str = "daily") -> dict:
    username = _safe_username(username)
    report_type = "weekly" if report_type == "weekly" else "daily"
    report = market_reporter.generate(report_type=report_type)
    reports = _read_market_reports(username=username, limit=50)
    reports.insert(0, report)
    _write_market_reports(reports, username=username)
    _append_automation_log(username, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type": f"market_{report_type}_report",
        "summary": {
            "environment": report.get("environment", {}).get("label"),
            "score": report.get("environment", {}).get("score"),
            "report_id": report.get("id"),
        },
    })
    _push_notification(f"{report['title']}已生成：{report.get('environment', {}).get('label', '-')}", username=username, level="info")
    return report


def _trim_json_list_file(path: Path, limit: int) -> int:
    return trim_json_list_file(path, limit, _read_json_file, _write_json_file)


def _create_user_backup(username: str) -> str | None:
    user_dir = _user_dir(username)
    backup_dir = user_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{_safe_username(username)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    files = [
        "alerts.json",
        "analysis_history.json",
        "automation_log.json",
        "automations.json",
        "holdings.json",
        "market_reports.json",
        "notifications.json",
    ]
    wrote_file = False
    with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in files:
            path = user_dir / name
            if path.exists():
                archive.write(path, arcname=name)
                wrote_file = True
        if SQLITE_FILE.exists():
            archive.write(SQLITE_FILE, arcname="quant_app.sqlite")
            wrote_file = True
    if not wrote_file:
        backup_path.unlink(missing_ok=True)
        return None
    backups = sorted(backup_dir.glob("*.zip"), key=lambda item: item.stat().st_mtime, reverse=True)
    for old_backup in backups[10:]:
        try:
            old_backup.unlink()
        except OSError:
            continue
    return str(backup_path.relative_to(BASE_DIR))


def _run_system_maintenance(username: str) -> None:
    username = _safe_username(username)
    backup_path = _create_user_backup(username)
    trimmed_logs = _trim_json_list_file(_user_file(username, "automation_log.json"), 100)
    trimmed_notifications = _trim_json_list_file(_user_file(username, "notifications.json"), 100)
    removed_cache = _cleanup_old_files(DATA_DIR / "cache", ("*.csv",), older_than_days=14)
    removed_logs = _cleanup_old_files(BASE_DIR / "logs", ("*.log",), older_than_days=30)

    enabled_jobs = [item for item in _read_automations(username=username) if item.get("enabled", True)]
    scheduled_ids = {job.id for job in scheduler.get_jobs()}
    missing_jobs = [
        item.get("id", item.get("job_type", "unknown"))
        for item in enabled_jobs
        if f"{username}:{item.get('id')}" not in scheduled_ids
    ]
    if missing_jobs:
        _reload_user_jobs(username)

    summary = {
        "backup": backup_path or "no_data",
        "trimmed_logs": trimmed_logs,
        "trimmed_notifications": trimmed_notifications,
        "removed_cache_files": removed_cache,
        "removed_log_files": removed_logs,
        "reloaded_missing_jobs": missing_jobs,
    }
    _append_automation_log(username, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type": "system_maintenance",
        "summary": summary,
    })
    if missing_jobs:
        _push_notification(f"自动维护已恢复任务：{', '.join(missing_jobs)}", username=username, level="alert")


def _run_max_history_refresh(username: str) -> None:
    targets = discover_targets([DATA_DIR / "cache", DATA_DIR / "cleaned"])
    summary = []
    for target in targets:
        try:
            _, rows, start, end = refresh_target(agent.data_fetcher, target, DATA_DIR / "cleaned")
            summary.append({
                "market": target.market,
                "symbol": target.symbol,
                "rows": rows,
                "start": start,
                "end": end,
                "status": "ok",
            })
        except Exception as exc:
            summary.append({
                "market": target.market,
                "symbol": target.symbol,
                "status": "error",
                "error": str(exc),
            })
    _append_automation_log(username, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type": "max_history_refresh",
        "summary": summary,
    })
    if summary:
        ok_count = sum(1 for item in summary if item.get("status") == "ok")
        _push_notification(f"最大历史数据刷新完成：{ok_count}/{len(summary)} 个标的成功。", username=username, level="info")


def _validate_curve_points(points: list[dict], initial_cash: float, total_return: float, label: str) -> None:
    if not points:
        raise RuntimeError(f"{label} curve is empty.")
    first = points[0]["value"]
    last = points[-1]["value"]
    if abs(first - initial_cash) > max(1.0, initial_cash * 0.001):
        raise RuntimeError(f"{label} curve starts from an unexpected value: {first}")
    expected_last = initial_cash * (1 + total_return)
    if abs(last - expected_last) > max(1.0, abs(expected_last) * 0.001):
        raise RuntimeError(f"{label} curve does not match backtest return.")


def _stock_fundamental_fallback(symbol: str, market: str, period: str, error: Exception, use_ai: bool, username: str | None = None) -> dict:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        print("\nMarket price data is temporarily unavailable; using fundamental fallback mode.")
        print(f"Reason: {_friendly_error(error)}")
        val_data = None
        try:
            val_data = fetch_stock_value(symbol, market)
        except Exception:
            val_data = None
        if val_data:
            print(format_value_report(val_data))
        else:
            print(format_value_report({
                "market": market,
                "symbol": symbol,
                "name": symbol,
            }))
        print(agent._format_cross_asset_valuation(market, val_data))
        print("\nTechnical chart and backtest are unavailable until market data recovers.")

    analysis_result = {
        "symbol": symbol,
        "market": market,
        "period": period,
        "latest_price": "",
        "data_range": "market data unavailable",
        "data_points": 0,
        "log": buffer.getvalue(),
        "analysis_image": None,
        "equity_image": None,
        "equity_points": [],
        "benchmark_points": [],
    }
    standard_report = build_report_from_analysis(
        analysis_result,
        source_records=_analysis_source_records(analysis_result, username=username or _current_user()),
    )
    _save_standard_research_report(standard_report, username=username or _current_user())
    analysis_result["standard_report_id"] = standard_report["id"]
    analysis_result["standard_report_url"] = "/research_report"

    from datetime import datetime
    _write_history_item({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "symbol": analysis_result["symbol"],
        "market": analysis_result["market"],
        "period": analysis_result["period"],
        "use_ai": bool(use_ai),
        "latest_price": "-",
        "data_range": analysis_result["data_range"],
        "data_points": analysis_result["data_points"],
        "analysis_image": None,
        "standard_report_id": analysis_result["standard_report_id"],
    }, username=username or _current_user())
    return analysis_result


def _run_analysis(
    symbol: str,
    market: str,
    period: str,
    use_ai: bool,
    force_refresh: bool = False,
    username: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    username = username or _current_user()
    buffer = io.StringIO()
    equity_points = []
    benchmark_points = []
    analysis_path = None
    with redirect_stdout(buffer):
        try:
            result = agent.analyze(
                symbol=symbol,
                market=market,
                period=period,
                use_ai=use_ai,
                force_refresh=force_refresh,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as exc:
            if market in ("a_stock", "us_stock"):
                return _stock_fundamental_fallback(symbol, market, period, exc, use_ai, username=username)
            raise
        analysis_path = visualizer.plot_analysis(result["df"], result["symbol"], save=True)
        from datetime import datetime
        if analysis_path:
            src = Path(analysis_path)
            if src.exists():
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                safe_symbol = result["symbol"].replace("-", "_")
                safe_user = _safe_username(username) if username else "guest"
                unique_path = REPORTS_DIR / f"{safe_user}_{safe_symbol}_{result['market']}_{period}_{stamp}_analysis.png"
                shutil.copy2(src, unique_path)
                analysis_path = str(unique_path)
        equity_path = None
        if result.get("backtest"):
            equity_curve = result["backtest"].equity_curve.dropna()
            equity_points = [
                {"date": idx.strftime("%Y-%m-%d"), "value": round(float(value), 2)}
                for idx, value in equity_curve.items()
            ]
            _validate_curve_points(
                equity_points,
                agent.config["backtest"]["initial_cash"],
                result["backtest"].total_return,
                "绛栫暐",
            )
        if result.get("benchmark"):
            benchmark_curve = result["benchmark"].equity_curve.dropna()
            benchmark_points = [
                {"date": idx.strftime("%Y-%m-%d"), "value": round(float(value), 2)}
                for idx, value in benchmark_curve.items()
            ]
            _validate_curve_points(
                benchmark_points,
                agent.config["backtest"]["initial_cash"],
                result["benchmark"].total_return,
                "涔板叆鎸佹湁",
            )

    latest_price = result["df"]["close"].iloc[-1] if not result["df"].empty else ""
    data_start = result["df"].index.min().strftime("%Y-%m-%d") if not result["df"].empty else "-"
    data_end = result["df"].index.max().strftime("%Y-%m-%d") if not result["df"].empty else "-"
    analysis_result = {
        "symbol": result["symbol"],
        "market": result["market"],
        "period": period,
        "latest_price": f"{latest_price:.4f}" if latest_price != "" else "",
        "data_range": f"{data_start} 鑷?{data_end}",
        "data_points": len(result["df"]),
        "log": buffer.getvalue(),
        "analysis_image": _to_image_url(analysis_path),
        "equity_image": _to_image_url(equity_path),
        "equity_points": equity_points,
        "benchmark_points": benchmark_points,
    }
    standard_report = build_report_from_analysis(
        analysis_result,
        source_records=_analysis_source_records(analysis_result, username=username),
    )
    _save_standard_research_report(standard_report, username=username)
    analysis_result["standard_report_id"] = standard_report["id"]
    analysis_result["standard_report_url"] = "/research_report"

    from datetime import datetime
    _write_history_item({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "symbol": analysis_result["symbol"],
        "market": analysis_result["market"],
        "period": analysis_result["period"],
        "use_ai": bool(use_ai),
        "latest_price": analysis_result["latest_price"] or "-",
        "data_range": analysis_result["data_range"],
        "data_points": analysis_result["data_points"],
        "analysis_image": analysis_result["analysis_image"],
        "standard_report_id": analysis_result["standard_report_id"],
    }, username=username)

    return analysis_result


def _friendly_error(exc: Exception) -> str:
    message = str(exc).strip() or "操作失败"
    if "fund" in message.lower():
        return f"{message}。请检查代码是否正确，或稍后再试。"
    if any(key in message for key in (
        "A鑲℃暟鎹簮杩炴帴澶辫触",
        "璇锋眰涓滄柟璐㈠瘜 API 澶辫触",
        "API 杩斿洖閿欒",
        "ProxyError",
        "Unable to connect to proxy",
        "Remote end closed connection",
        "Max retries exceeded",
        "HTTPSConnectionPool",
    )):
        return "Data source connection failed. This is usually a temporary network or proxy issue."
    return f"操作失败：{message}"


def _fetch_latest_snapshot(symbol: str, market: str, period: str = "3mo") -> dict | None:
    try:
        df = agent.data_fetcher.fetch(symbol=symbol, market=market, period=period)
        df = add_all_indicators(df, config=agent.config.get("strategy"))
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        return {
            "symbol": symbol,
            "market": market,
            "price": float(latest["close"]),
            "ma_fast": float(latest.get("MA10", latest["close"])),
            "ma_slow": float(latest.get("MA30", latest["close"])),
            "prev_price": float(prev["close"]),
            "prev_ma_fast": float(prev.get("MA10", prev["close"])),
            "prev_ma_slow": float(prev.get("MA30", prev["close"])),
            "signals": generate_signal_summary(df),
        }
    except Exception:
        return None


def _evaluate_alerts(username: str | None = None) -> list[str]:
    username = username or _current_user()
    if not username:
        return []
    alerts = _read_alerts(username=username)
    triggered_messages = []
    changed = False
    for alert in alerts:
        if not alert.get("enabled", True):
            continue
        snapshot = _fetch_latest_snapshot(alert.get("symbol", ""), alert.get("market", "fund"), period="3mo")
        if not snapshot:
            continue
        price = snapshot["price"]
        target = float(alert.get("target_price", 0) or 0)
        condition = alert.get("condition", "lte")
        hit = (condition == "lte" and price <= target) or (condition == "gte" and price >= target)
        if hit:
            already = alert.get("last_triggered_at")
            direction = "低于" if condition == "lte" else "高于"
            message = f"价格预警触发：{alert.get('symbol', '')} 当前价 {price:.4f}，已{direction}目标价 {target:.4f}"
            if not already:
                alert["last_triggered_at"] = datetime.now().isoformat()
                triggered_messages.append(message)
                _push_notification(message, username=username, level="alert")
                changed = True
        else:
            if alert.get("last_triggered_at"):
                alert["last_triggered_at"] = ""
                changed = True
    if changed:
        _write_alerts(alerts, username=username)
    return triggered_messages


def _evaluate_moving_average_breaks(username: str) -> list[str]:
    mgr = HoldingsManager(filepath=str(_user_file(username, "holdings.json")), username=_safe_username(username))
    messages = []
    for holding in mgr.list_all():
        snapshot = _fetch_latest_snapshot(holding.symbol, holding.market, period="3mo")
        if not snapshot:
            continue
        crossed_up = snapshot["prev_price"] <= snapshot["prev_ma_fast"] and snapshot["price"] > snapshot["ma_fast"]
        crossed_down = snapshot["prev_price"] >= snapshot["prev_ma_fast"] and snapshot["price"] < snapshot["ma_fast"]
        if crossed_up:
            messages.append(f"{holding.symbol} crossed above MA10 at {snapshot['price']:.4f}")
        elif crossed_down:
            messages.append(f"{holding.symbol} crossed below MA10 at {snapshot['price']:.4f}")
    for msg in messages:
        _push_notification(f"MA alert: {msg}", username=username, level="info")
    return messages


def _run_daily_holdings_scan(username: str) -> None:
    mgr = HoldingsManager(filepath=str(_user_file(username, "holdings.json")), username=_safe_username(username))
    summary = []
    for holding in mgr.list_all():
        try:
            analysis = _run_analysis(
                holding.symbol,
                holding.market,
                "max",
                use_ai=False,
                force_refresh=False,
                username=username,
            )
            summary.append({
                "symbol": holding.symbol,
                "market": holding.market,
                "price": analysis.get("latest_price") or "-",
                "data_points": analysis.get("data_points", 0),
                "analysis_image": analysis.get("analysis_image"),
                "status": "ok",
            })
        except Exception as exc:
            snapshot = _fetch_latest_snapshot(holding.symbol, holding.market, period="1y")
            item = {
                "symbol": holding.symbol,
                "market": holding.market,
                "status": "snapshot" if snapshot else "error",
            }
            if snapshot:
                item.update({"price": round(snapshot["price"], 4), "signals": snapshot["signals"]})
            else:
                item["error"] = str(exc)
            summary.append(item)
    if summary:
        _append_automation_log(username, {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "type": "daily_holdings_scan",
            "summary": summary,
        })
        _push_notification(f"Daily holdings scan completed for {len(summary)} symbols.", username=username, level="info")


def _run_daily_digest(username: str) -> None:
    history = _read_history(username=username, limit=5)
    latest_symbols = [item.get("symbol", "") for item in history[:3] if item.get("symbol")]
    _append_automation_log(username, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type": "daily_digest",
        "summary": {
            "recent_symbols": latest_symbols,
            "history_count": len(_read_history(username=username, limit=100)),
            "alert_count": len(_read_alerts(username=username)),
        },
    })
    _push_notification("Daily digest generated.", username=username, level="info")


def _automation_job_runner(username: str, job_type: str) -> None:
    try:
        app.logger.info("automation job started: user=%s job=%s", username, job_type)
        if job_type == "price_alert_scan":
            hits = _evaluate_alerts(username=username)
            ma_hits = _evaluate_moving_average_breaks(username)
            _append_automation_log(username, {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "type": job_type,
                "summary": {"price_alert_hits": hits, "ma_hits": ma_hits},
            })
        elif job_type == "daily_holdings_scan":
            _run_daily_holdings_scan(username)
        elif job_type == "daily_digest":
            _run_daily_digest(username)
        elif job_type == "market_daily_report":
            _run_market_report(username, "daily")
        elif job_type == "market_weekly_report":
            _run_market_report(username, "weekly")
        elif job_type == "system_maintenance":
            _run_system_maintenance(username)
        elif job_type == "max_history_refresh":
            _run_max_history_refresh(username)
        app.logger.info("automation job finished: user=%s job=%s", username, job_type)
    except Exception as exc:
        app.logger.exception("automation job failed: user=%s job=%s", username, job_type)
        _append_automation_log(username, {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "type": job_type,
            "summary": {"error": str(exc)},
        })


def _scheduler_event_listener(event) -> None:
    job_id = getattr(event, "job_id", "unknown")
    if event.code == EVENT_JOB_MISSED:
        app.logger.warning("scheduler missed job: %s", job_id)
    elif event.code == EVENT_JOB_ERROR:
        app.logger.error("scheduler job error: %s %s", job_id, getattr(event, "exception", ""))


def _reload_user_jobs(username: str) -> None:
    username = _safe_username(username)
    for job in scheduler.get_jobs():
        if job.id.startswith(f"{username}:"):
            scheduler.remove_job(job.id)
    for item in _read_automations(username=username):
        if not item.get("enabled", True):
            continue
        job_type = item.get("job_type")
        if job_type in ("price_alert_scan", "system_maintenance", "max_history_refresh"):
            default_minutes = 1440 if job_type == "max_history_refresh" else (60 if job_type == "system_maintenance" else 15)
            minutes = _bounded_int(item.get("interval_minutes", default_minutes), default_minutes, 1, 10080)
            scheduler.add_job(
                _automation_job_runner,
                "interval",
                minutes=minutes,
                id=f"{username}:{item['id']}",
                replace_existing=True,
                kwargs={"username": username, "job_type": job_type},
            )
        elif job_type == "market_weekly_report":
            run_time = _normalize_run_time(item.get("run_time", "16:30"), default="16:30")
            hour, minute = [int(x) for x in run_time.split(":", 1)]
            scheduler.add_job(
                _automation_job_runner,
                "cron",
                day_of_week="fri",
                hour=hour,
                minute=minute,
                id=f"{username}:{item['id']}",
                replace_existing=True,
                kwargs={"username": username, "job_type": job_type},
            )
        else:
            run_time = _normalize_run_time(item.get("run_time", "09:00"))
            hour, minute = [int(x) for x in run_time.split(":", 1)]
            scheduler.add_job(
                _automation_job_runner,
                "cron",
                hour=hour,
                minute=minute,
                id=f"{username}:{item['id']}",
                replace_existing=True,
                kwargs={"username": username, "job_type": job_type},
            )


def _reload_all_jobs() -> None:
    USERSPACE_DIR.mkdir(parents=True, exist_ok=True)
    for user_dir in USERSPACE_DIR.iterdir():
        if user_dir.is_dir():
            _reload_user_jobs(user_dir.name)


def _current_holdings_dataframe() -> list[dict]:
    mgr = _current_holdings_mgr()
    return [
        {
            "username": _safe_username(_current_user()),
            "symbol": h.symbol,
            "market": h.market,
            "quantity": h.quantity,
            "avg_cost": h.avg_cost,
            "buy_date": h.buy_date,
            "notes": h.notes,
            "added_at": h.added_at,
        }
        for h in mgr.list_all()
    ]


def _export_rows_to_files(rows: list[dict], stem: str, username: str | None = None):
    username = username or _current_user()
    export_dir = _user_dir(username) / "exports"
    safe_stem = safe_export_stem(stem)
    unique_stem = f"{safe_stem}_{uuid4().hex[:10]}"
    return build_export_files(rows, unique_stem, export_dir)


def _send_user_export(path: Path, username: str):
    export_dir = (_user_dir(username) / "exports").resolve()
    resolved = path.resolve()
    if export_dir not in resolved.parents:
        return "Not found", 404
    return send_file(resolved, as_attachment=True)


def _handle_prompt(prompt: str) -> tuple[dict | None, str | None, str | None, dict]:
    parsed = parse_natural_language_command(prompt, agent)
    wants_ai = any(k in prompt.lower() for k in ("ai", "llm", "report"))
    form = {
        "prompt": prompt,
        "symbol": "",
        "market": "fund",
        "period": "max",
        "use_ai": wants_ai,
    }

    intent = parsed.get("intent")
    if intent == "analyze":
        market = _normalize_market(parsed.get("market") or "fund")
        symbol = _normalize_symbol(parsed.get("symbol") or "", market)
        period = _normalize_period(parsed.get("period") or "max")
        use_ai = bool(parsed.get("use_ai", False) and wants_ai)
        form.update({"symbol": symbol, "market": market, "period": period, "use_ai": use_ai})
        return _run_analysis(symbol, market, period, use_ai), None, None, form

    if intent == "holdings":
        username = _current_user()
        if not username:
            return None, "请先登录后再查看持仓。", None, form
        holdings = _current_holdings_mgr().list_all()
        if not holdings:
            return None, "暂无持仓。", None, form
        lines = ["当前持仓："]
        for h in holdings:
            lines.append(f"- {h.symbol} ({h.market}) qty:{h.quantity} cost:{h.avg_cost}")
        return None, "\n".join(lines), None, form

    if intent == "help":
        return None, "Try: analyze 002982 fund, analyze NVDA 1mo, or view my holdings.", None, form

    if intent == "quit":
        return None, "The web version does not need a quit command.", None, form

    return None, parsed.get("reply") or "I did not recognize that request yet.", None, form


if not scheduler.running:
    scheduler.add_listener(_scheduler_event_listener, EVENT_JOB_ERROR | EVENT_JOB_MISSED)
    scheduler.start()
    sqlite_store.migrate_userspace(USERSPACE_DIR)
    _reload_all_jobs()




register_system_routes(app, {
    "scheduler": scheduler,
    "reports_dir": lambda: REPORTS_DIR,
    "current_user": _current_user,
    "is_report_visible_to_user": _is_report_visible_to_user,
    "read_history": _read_history,
    "cache_count": _cache_count,
    "agent": agent,
    "current_holdings_dataframe": _current_holdings_dataframe,
    "read_alerts": _read_alerts,
    "export_rows_to_files": _export_rows_to_files,
    "send_user_export": _send_user_export,
    "safe_username": _safe_username,
})

register_auth_routes(app, {
    "load_users": _load_users,
    "save_users": _save_users,
    "verify_password": _verify_password,
    "hash_password": _hash_password,
    "is_valid_username": _is_valid_username,
    "login_blocked_until": _login_blocked_until,
    "record_login_failure": _record_login_failure,
    "clear_login_failures": _clear_login_failures,
    "ensure_user_space": _ensure_user_space,
    "reload_user_jobs": _reload_user_jobs,
})

register_research_routes(app, {
    "agent": agent,
    "normalize_market": _normalize_market,
    "normalize_period": _normalize_period,
    "normalize_symbol": _normalize_symbol,
    "friendly_error": _friendly_error,
    "current_user": _current_user,
    "ensure_user_space": _ensure_user_space,
    "normalize_run_time": _normalize_run_time,
    "run_market_report": _run_market_report,
    "upsert_automation_items": _upsert_automation_items,
    "read_market_reports": _read_market_reports,
    "read_automations": _read_automations,
    "economic_history_events": ECONOMIC_HISTORY_EVENTS,
    "valuation_metrics": VALUATION_METRICS,
})

register_report_routes(app, {
    "current_user": _current_user,
    "ensure_user_space": _ensure_user_space,
    "user_dir": _user_dir,
    "safe_username": _safe_username,
    "friendly_error": _friendly_error,
    "read_history": _read_history,
    "agent": agent,
})

register_main_routes(app, {
    "current_user": _current_user,
    "ensure_user_space": _ensure_user_space,
    "normalize_market": _normalize_market,
    "normalize_symbol": _normalize_symbol,
    "normalize_period": _normalize_period,
    "run_analysis": _run_analysis,
    "handle_prompt": _handle_prompt,
    "parse_bounded_float": _parse_bounded_float,
    "validate_buy_date": _validate_buy_date,
    "current_holdings_mgr": _current_holdings_mgr,
    "sync_sqlite_user_data": _sync_sqlite_user_data,
    "read_alerts": _read_alerts,
    "write_alerts": _write_alerts,
    "evaluate_alerts": _evaluate_alerts,
    "read_automations": _read_automations,
    "write_automations": _write_automations,
    "reload_user_jobs": _reload_user_jobs,
    "automation_job_runner": _automation_job_runner,
    "friendly_error": _friendly_error,
    "consume_notifications": _consume_notifications,
    "read_history": _read_history,
    "read_automation_log": _read_automation_log,
    "cache_count": _cache_count,
    "list_recent_reports": _list_recent_reports,
    "bounded_int": _bounded_int,
    "normalize_run_time": _normalize_run_time,
    "user_dir": _user_dir,
    "shared_reports_dir": lambda: DATA_DIR / "shared_reports",
    "agent": agent,
})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    host = os.getenv("HOST", "127.0.0.1")
    if sys.stdout:
        print(f"Web console started: http://{host}:{port}")
    app.run(host=host, port=port, debug=False)





