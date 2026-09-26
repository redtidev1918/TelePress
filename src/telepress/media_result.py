"""Structured, provider-qualified media result.

New in this version. It does NOT replace :class:`~telepress.uploader.UploadResult`
or the ``str`` URL returned by ``ImageUploader.upload()`` / ``ImageUploader`` host
``upload()`` — those keep their existing return types and semantics unchanged.

``ResolvedMedia`` is an opt-in, richer structured result that a caller can request
from the new ``ImageUploader.resolve()`` entry point. It carries the canonical
``url`` plus structured metadata and a provider-qualified ``media_uri``
(``provider://id``) so a media id is never a bare string detached from its provider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResolvedMedia:
    """Standard result describing a media item after it has been resolved
    (uploaded or proxied), ready for a publisher to consume.

    ``url`` is the canonical public URL — identical concept to what ``upload()``
    returns today, kept as a plain string so any existing consumer that uses the
    URL directly continues to work.

    ``media_uri`` is a provider-qualified id of the form ``<provider>://<id>``.
    It is derived lazily from :attr:`provider` and :attr:`media_id`; either may be
    ``None``, in which case ``media_uri`` is also ``None`` (we never fabricate
    ids the underlying host did not give us).
    """

    url: str
    provider: Optional[str] = None
    media_id: Optional[str] = None
    mime_type: Optional[str] = None
    filename: Optional[str] = None
    size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    source_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @property
    def media_uri(self) -> Optional[str]:
        """``<provider>://<media_id>`` when both are known, else ``None``."""
        if self.provider and self.media_id:
            return f"{self.provider}://{self.media_id}"
        return None


def provider_qualify(provider: Optional[str], media_id: Optional[str]) -> Optional[str]:
    """Return ``<provider>://<media_id>`` or ``None`` when either part is missing.

    Convenience helper so callers do not need to construct :class:`ResolvedMedia`
    just to build a qualified id (or to embed it in existing log lines / results).
    """
    if provider and media_id:
        return f"{provider}://{media_id}"
    return None