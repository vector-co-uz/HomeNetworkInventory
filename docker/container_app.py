"""Configure the upstream ASGI app from container environment variables.

This adapter intentionally keeps Docker-specific behavior outside ``app/`` so
upstream application updates can be merged without repeatedly editing source
files maintained by the original author.
"""

from __future__ import annotations

import os
import re
from typing import Any

from app.config import settings


_TRUE_VALUES = {"true", "1", "yes", "on"}
_FALSE_VALUES = {"false", "0", "no", "off"}


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name, str(default)).strip().lower()
    if value not in _TRUE_VALUES | _FALSE_VALUES:
        raise ValueError(f"{name} must be true or false")
    return value in _TRUE_VALUES


session_secret = os.getenv("SESSION_SECRET", "").strip()
if len(session_secret) < 32:
    raise ValueError("Set SESSION_SECRET to a random string of at least 32 characters")

session_https_only = _env_bool("SESSION_HTTPS_ONLY", True)

# These attributes are consumed by the unmodified upstream modules when they
# are imported below. ``cookie_secure`` supports upstream versions that use
# that name, while ``session_https_only`` supports versions that expose it.
settings.database_url = os.getenv("DATABASE_URL", "sqlite:////data/home_network.db")
settings.session_secret = session_secret
settings.session_https_only = session_https_only
settings.cookie_secure = session_https_only
settings.session_timeout_seconds = int(os.getenv("SESSION_TIMEOUT_SECONDS", "7200"))

from app.main import app as upstream_app  # noqa: E402


class CookieSecurityAdapter:
    """Remove Secure from upstream cookies only for explicitly configured HTTP."""

    def __init__(self, app: Any, secure: bool) -> None:
        self.app = app
        self.secure = secure

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if self.secure or scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_without_secure_cookie(message: dict) -> None:
            if message["type"] == "http.response.start":
                message = dict(message)
                message["headers"] = [
                    (name, re.sub(rb";\s*Secure(?=;|$)", b"", value, flags=re.IGNORECASE))
                    if name.lower() == b"set-cookie"
                    else (name, value)
                    for name, value in message.get("headers", [])
                ]
            await send(message)

        await self.app(scope, receive, send_without_secure_cookie)


app = CookieSecurityAdapter(upstream_app, secure=session_https_only)
