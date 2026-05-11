"""Console helpers shared by command-line entry points."""

from __future__ import annotations

import sys


def configure_console_output() -> None:
    """Avoid UnicodeEncodeError in legacy Windows consoles."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None or not hasattr(stream, "reconfigure"):
            continue
        try:
            stream.reconfigure(errors="replace")
        except Exception:
            pass
