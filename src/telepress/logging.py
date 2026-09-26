"""Minimal structured logging for TelePress.

New in this version. Uses only the standard-library :mod:`logging` module and a
single module logger (``telepress``). Existing call sites that use ``print`` are
left untouched — this is opt-in for new code paths, not a rewrite of the log
channel. There is deliberately **no** OpenTelemetry / Prometheus / external
tracing dependency.
"""

from __future__ import annotations

import logging

# One logger for the whole library; consumers can attach handlers/formatters
# and set the level via the standard logging API.
logger = logging.getLogger("telepress")


def event(event: str, **fields) -> None:
    """Emit a structured log line as ``event=... key=value ...`` at INFO.

    The key format is intentionally greppable in CLI / Docker / CI output:

        telepress: event=upload_started provider=catbox attempt=1

    ``fields`` values are repr'd safely (never secrets — callers must not pass
    credentials here).
    """
    if not logger.isEnabledFor(logging.INFO):
        return
    parts = [f"event={event}"]
    parts.extend(f"{k}={v}" for k, v in fields.items())
    logger.info("telepress: %s", " ".join(parts))