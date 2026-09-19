"""Pixiv CDN media proxy rewrite (fixed-upstream, SSRF-safe).

TelePress may be configured with ``TELEPRESS_PIXIV_PROXY_BASE`` pointing at a
Cloudflare Worker that proxies *only* ``https://i.pximg.net`` and adds Pixiv's
Referer header. When present, Pixiv source URLs in a rich-novel ``manifest``
are rewritten to ``<base>/pixiv/<path>`` and used directly instead of uploading
the local image to an image host. No manifest entry or no proxy base falls back
to the existing image-host upload path.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlsplit, urlunsplit

PIXIV_CDN_HOST = "i.pximg.net"
PIXIV_CDN_PREFIX = f"https://{PIXIV_CDN_HOST}/"


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


def pixiv_proxy_base() -> str:
    """Proxy base URL (trailing slash stripped), or '' when disabled."""
    return os.getenv("TELEPRESS_PIXIV_PROXY_BASE", "").strip().rstrip("/")


def pixiv_proxy_url(source: str) -> Optional[str]:
    """Rewrite a Pixiv CDN URL to the proxy path, or ``None``.

    Only ``https://i.pximg.net/...`` sources are eligible; anything else is
    left untouched so this never becomes an open proxy or SSRF surface.
    """
    base = pixiv_proxy_base()
    if not base or not source or not source.startswith(PIXIV_CDN_PREFIX):
        return None
    parts = urlsplit(source)
    if parts.scheme != "https" or parts.netloc != PIXIV_CDN_HOST:
        return None
    path = parts.path.lstrip("/")
    if not path:
        return None
    target = f"{base}/pixiv/{path}"
    if parts.query:
        target = urlunsplit(("", "", target, parts.query, ""))
    return target
