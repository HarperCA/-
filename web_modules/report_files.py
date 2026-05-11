# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

from flask import url_for


def to_image_url(path_str: str | None, reports_dir: Path, serve_endpoint: str = "serve_report") -> str | None:
    if not path_str:
        return None
    path = Path(path_str)
    try:
        rel_name = path.relative_to(reports_dir).as_posix()
    except ValueError:
        rel_name = path.name
    return url_for(serve_endpoint, filename=rel_name)


def report_prefix_for_user(username: str | None, safe_username) -> str:
    return f"{safe_username(username)}_"


def is_report_visible_to_user(filename: str, username: str | None, safe_username) -> bool:
    if not filename.endswith(".png"):
        return False
    if username:
        return filename.startswith(report_prefix_for_user(username, safe_username))
    return filename.startswith("guest_")


def list_recent_reports(reports_dir: Path, username: str | None, safe_username, to_url, limit: int = 8) -> list[dict]:
    if not reports_dir.exists():
        return []
    prefix = report_prefix_for_user(username, safe_username)
    visible_reports = [
        path
        for path in reports_dir.glob(f"{prefix}*_analysis.png")
        if is_report_visible_to_user(path.name, username, safe_username)
    ]
    items = []
    for path in sorted(visible_reports, key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
        stem = path.stem
        parts = stem.split("_")
        items.append({
            "time": path.stat().st_mtime,
            "name": path.name,
            "symbol": parts[1] if len(parts) > 1 else stem,
            "market": parts[2] if len(parts) > 2 else "",
            "url": to_url(str(path)),
        })
    return items
