"""Generic CDN media proxy rewrite (fixed-upstream allowlist, SSRF-safe).

TelePress can rewrite rich-novel manifest ``source`` URLs to a user-supplied
proxy base instead of uploading them to an image host. The proxy endpoint is
generic and described entirely by the operator:

- ``TELEPRESS_MEDIA_PROXY_BASE``   proxy base URL, e.g. ``https://media.example.com``
- ``TELEPRESS_MEDIA_PROXY_HOSTS``  comma-separated allowlist of upstream CDN hosts
  (e.g. ``i.pximg.net, i.etsystatic.com``); only https sources whose host is in
  this list are eligible
- ``TELEPRESS_MEDIA_PROXY_PATH_PREFIX`` (optional, default ``media``)

Rewritten URL is ``<base>/<prefix>/<host>/<path>`` for the generic config.

Backwards compatibility: setting only the legacy ``TELEPRESS_PIXIV_PROXY_BASE``
keeps the original behavior — allowlist ``i.pximg.net`` and rewrite to
``<base>/pixiv/<path>``.

No proxy base / no matching allowlist entry falls back to the normal
image-host upload path. A failed or unlisted host is never treated as a proxy
target, so this cannot become an open proxy or SSRF surface.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Set
from urllib.parse import urlsplit, urlunsplit

LEGACY_PIXIV_HOST = "i.pximg.net"


@dataclass
class MediaReference:
    """Canonical media reference for a rich-novel manifest entry."""

    local_ref: str
    source_url: Optional[str] = None
    asset_id: Optional[str] = None
    local_path: Optional[str] = None


def reference_from_entry(entry: dict) -> Optional[MediaReference]:
    """Accept both the legacy ``{local, source}`` and new ``{assetId, sourceUrl}`` shapes."""
    if not isinstance(entry, dict):
        return None
    local = entry.get("local") or entry.get("local_ref") or entry.get("localPath")
    if not local:
        return None
    source = entry.get("sourceUrl") or entry.get("source_url") or entry.get("source")
    return MediaReference(
        local_ref=str(local),
        source_url=str(source) if source else None,
        asset_id=entry.get("assetId") or entry.get("asset_id"),
        local_path=entry.get("localPath") or entry.get("local_path"),
    )


def _generic_mode() -> bool:
    return bool(os.getenv("TELEPRESS_MEDIA_PROXY_BASE", "").strip())


def proxy_base() -> str:
    """Proxy base URL (trailing slash stripped), or '' when disabled."""
    generic = os.getenv("TELEPRESS_MEDIA_PROXY_BASE", "").strip().rstrip("/")
    if generic:
        return generic
    return os.getenv("TELEPRESS_PIXIV_PROXY_BASE", "").strip().rstrip("/")


def allowed_hosts() -> Set[str]:
    """:return: normalized allowed source hosts, or empty set when unset."""
    base = proxy_base()
    if not base:
        return set()
    hosts = set()
    raw = os.getenv("TELEPRESS_MEDIA_PROXY_HOSTS", "").strip()
    for item in raw.split(","):
        item = item.strip().lower()
        if item:
            hosts.add(item)
    if not _generic_mode():
        # Legacy TELEPRESS_PIXIV_PROXY_BASE keeps the original i.pximg.net allowlist.
        hosts.add(LEGACY_PIXIV_HOST)
    return hosts


def path_prefix() -> str:
    """Prefix used in the rewritten path; ``pixiv`` for the legacy alias."""
    if not _generic_mode():
        return "pixiv"
    return os.getenv("TELEPRESS_MEDIA_PROXY_PATH_PREFIX", "media").strip().strip("/") or "media"


def proxy_url(source: str) -> Optional[str]:
    """Rewrite an allowlisted CDN source URL to the proxy path, or ``None``.

    Only ``https`` URLs whose source host is in the configured allowlist are
    eligible; anything else returns ``None`` so the caller keeps the existing
    image-host fallback. Generic config rewrites to
    ``<base>/<prefix>/<host>/<path>``; the legacy alias rewrites to
    ``<base>/pixiv/<path>``.
    """
    base = proxy_base()
    if not base or not source:
        return None
    hosts = allowed_hosts()
    if not hosts:
        return None
    parts = urlsplit(source)
    if parts.scheme != "https":
        return None
    host = (parts.netloc or "").lower()
    if host not in hosts:
        return None
    path = parts.path.lstrip("/")
    if not path:
        return None
    prefix = path_prefix()
    if _generic_mode():
        target = f"{base}/{prefix}/{host}/{path}"
    else:
        target = f"{base}/{prefix}/{path}"
    if parts.query:
        target = urlunsplit(("", "", target, parts.query, ""))
    return target
