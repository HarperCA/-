# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path


def bounded_int(value, default: int, minimum: int = 1, maximum: int = 10080) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return min(max(parsed, minimum), maximum)


def normalize_run_time(value: str | None, default: str = "09:00") -> str:
    text = (value or default).strip()
    match = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", text)
    if not match:
        return default
    return f"{int(match.group(1)):02d}:{int(match.group(2)):02d}"


def cleanup_old_files(directory: Path, patterns: tuple[str, ...], older_than_days: int) -> int:
    if not directory.exists():
        return 0
    cutoff = datetime.now() - timedelta(days=older_than_days)
    removed = 0
    for pattern in patterns:
        for path in directory.glob(pattern):
            try:
                if path.is_file() and datetime.fromtimestamp(path.stat().st_mtime) < cutoff:
                    path.unlink()
                    removed += 1
            except OSError:
                continue
    return removed


def trim_json_list_file(path: Path, limit: int, read_json, write_json) -> int:
    data = read_json(path, [])
    if not isinstance(data, list) or len(data) <= limit:
        return 0
    write_json(path, data[:limit])
    return len(data) - limit
