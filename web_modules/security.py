# -*- coding: utf-8 -*-
from __future__ import annotations

import math
import re
from datetime import datetime, timedelta

from werkzeug.security import check_password_hash, generate_password_hash


LOGIN_FAILURE_LIMIT = 5
LOGIN_FAILURE_WINDOW = timedelta(minutes=15)
LOGIN_LOCKOUT = timedelta(minutes=5)
LOGIN_FAILURES: dict[str, list[datetime]] = {}


def legacy_hash_password(password: str, salt: str = None) -> tuple[str, str]:
    import hashlib
    import secrets

    if salt is None:
        salt = secrets.token_hex(8)
    hashed = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
    return hashed, salt


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(user: dict, password: str) -> bool:
    password_hash = user.get("password_hash", "")
    if not password_hash:
        return False
    if ":" in password_hash:
        try:
            return check_password_hash(password_hash, password)
        except Exception:
            return False
    legacy_hash, _ = legacy_hash_password(password, user.get("salt", ""))
    return legacy_hash == password_hash


def safe_username(username: str | None) -> str:
    base = (username or "guest").strip()
    base = re.sub(r"[^0-9A-Za-z_\-]+", "_", base)
    return base or "guest"


def is_valid_username(username: str) -> bool:
    return bool(re.fullmatch(r"[0-9A-Za-z_-]{3,20}", username or ""))


def login_key(username: str) -> str:
    return username.strip().lower()


def login_blocked_until(username: str) -> datetime | None:
    key = login_key(username)
    now = datetime.now()
    recent = [ts for ts in LOGIN_FAILURES.get(key, []) if now - ts <= LOGIN_FAILURE_WINDOW]
    LOGIN_FAILURES[key] = recent
    if len(recent) >= LOGIN_FAILURE_LIMIT:
        last_failure = max(recent)
        blocked_until = last_failure + LOGIN_LOCKOUT
        if now < blocked_until:
            return blocked_until
    return None


def record_login_failure(username: str) -> None:
    key = login_key(username)
    now = datetime.now()
    recent = [ts for ts in LOGIN_FAILURES.get(key, []) if now - ts <= LOGIN_FAILURE_WINDOW]
    recent.append(now)
    LOGIN_FAILURES[key] = recent


def clear_login_failures(username: str) -> None:
    LOGIN_FAILURES.pop(login_key(username), None)


def parse_bounded_float(value: str, label: str, minimum: float, maximum: float) -> float:
    try:
        parsed = float((value or "").strip())
    except (TypeError, ValueError):
        raise ValueError(f"{label}必须是数字")
    if not math.isfinite(parsed):
        raise ValueError(f"{label}必须是有限数字")
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{label}必须在 {minimum:g} 到 {maximum:g} 之间")
    return parsed


def validate_market(value: str) -> str:
    if value not in {"fund", "a_stock", "us_stock", "crypto"}:
        raise ValueError("市场类型无效")
    return value


def validate_period(value: str) -> str:
    allowed = {"1mo", "3mo", "6mo", "1y", "2y", "3y", "5y", "10y", "20y", "50y", "max"}
    if value not in allowed:
        raise ValueError("周期无效")
    return value


def validate_buy_date(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    datetime.strptime(value, "%Y-%m-%d")
    return value
