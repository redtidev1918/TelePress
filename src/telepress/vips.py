"""Libvips-backed, streaming image compression for TelePress.

The legacy Pillow path decoded the full source image into Python memory before
resizing/encoding, producing an unnecessary peak memory footprint for very
large images.  pyvips pipelines are lazy and demand-driven: ``thumbnail()``
performs a controlled downscale while the source is still being read, and the
final JPEG/WebP output is written straight to the retaining temporary file, so
a large source never has to materialize as a full Python ``Image`` / NumPy
array.

This module holds the production implementation and is exposed to callers
through ``telepress.utils.compress_image_to_size``.
"""
import os
import tempfile

import pyvips

from .exceptions import ConversionError

#: Largest edge (in pixels) a candidate is allowed to have.
MAX_SAFE_EDGE = 4096
#: Largest total pixel count (16 MP) a candidate is allowed to have.
MAX_SAFE_PIXELS = 16_777_216

# Formats we are willing to re-encode.  mimi-guess handled by libvips itself,
# this set follows the legacy behaviour of attempting anything that is not GIF.
SKIP_COMPRESSION_FORMATS = {'.gif'}

_OUT_JPEG = 'JPEG'
_OUT_WEBP = 'WEBP'

# Quality range used by the logarithmic quality search, mirroring the legacy
# "highest acceptable quality first" semantics.
_MAX_QUALITY = 95


def _safe_edge(width: int, height: int) -> int:
    """Compute a safe initial edge that never exceeds 4096 px nor 16 MP."""
    area_scale = min(1.0, (MAX_SAFE_PIXELS / max(1, width * height)) ** 0.5)
    edge_scale = min(1.0, MAX_SAFE_EDGE / max(width, height))
    scale = min(area_scale, edge_scale)
    return max(1, int(max(width, height) * scale))


def _prepare_for_jpeg(image: 'pyvips.Image') -> 'pyvips.Image':
    """Return a 3-band image suitable for JPEG/WebP encoding.

    Alpha is flattened onto white, single-band (greyscale) images are
    promoted to 3 bands, and anything with more than 3 bands (e.g. CMYK) is
    reduced to its first 3 bands.  The pipeline stays lazy.
    """
    if image.hasalpha():
        image = image.flatten(background=[255, 255, 255])
    if image.bands == 1:
        image = image.bandjoin([image, image])
    elif image.bands > 3:
        image = image.extract_band(0, n=3)
    return image


def _output_format(prefer_webp: bool):
    return (_OUT_WEBP, '.webp') if prefer_webp else (_OUT_JPEG, '.jpg')


def _binary_search_quality(low, high, probe, max_size):
    """Return the highest quality in ``[low, high]`` whose ``probe(q)``
    reports a file size <= ``max_size``.

    ``probe(quality)`` must return the on-disk size of the image encoded at
    that quality (a value > ``max_size`` means "too big").  Uses O(log N)
    encode attempts.  Returns ``None`` when no quality in the range fits.
    """
    best = None
    while low <= high:
        quality = (low + high) // 2
        size = probe(quality)
        if size <= max_size:
            best = quality
            low = quality + 1
        else:
            high = quality - 1
    return best


def _write_candidate(edge: int, out_format: str, quality: int,
                     image: 'pyvips.Image') -> str:
    """Encode ``image`` directly to a temporary file (no Python bytes buffer)."""
    out_ext = '.webp' if out_format == _OUT_WEBP else '.jpg'
    fd, path = tempfile.mkstemp(prefix='telepress-', suffix=out_ext)
    os.close(fd)
    try:
        # optimize_coding enables optimal Huffman tables for JPEG, matching the
        # legacy Pillow path which encoded with optimize=True.
        opts = {}
        if out_format == _OUT_JPEG:
            opts['optimize_coding'] = True
        image.write_to_file(path, Q=quality, strip=True, **opts)
        return path
    except Exception:
        _unlink_quiet(path)
        raise


def _search_at_edge(image_path, edge, out_format, max_size,
                    min_quality, created):
    """Try to fit the image at ``edge`` (long edge) under ``max_size``.

    Runs a logarithmic quality search at this edge.  Every candidate is written
    to its own temporary file (appended to ``created``) instead of being held in
    a Python buffer.  Returns the path of the best fitting candidate, or
    ``None`` if no quality fits.
    """
    def probe(quality):
        thumbnail = pyvips.Image.thumbnail(
            image_path, edge, height=edge, size='down')
        img = _prepare_for_jpeg(thumbnail)
        path = _write_candidate(edge, out_format, quality, img)
        created.append(path)
        return os.path.getsize(path)

    quality = _binary_search_quality(min_quality, _MAX_QUALITY, probe, max_size)
    if quality is None:
        return None

    # Re-encode once at the winning quality to hand back a pristine file that
    # is guaranteed <= max_size.
    thumbnail = pyvips.Image.thumbnail(
        image_path, edge, height=edge, size='down')
    img = _prepare_for_jpeg(thumbnail)
    path = _write_candidate(edge, out_format, quality, img)
    created.append(path)
    if os.path.getsize(path) > max_size:
        return None
    return path


def _unlink_quiet(path):
    try:
        if path and os.path.exists(path):
            os.unlink(path)
    except OSError:
        pass


def compress_image_to_size(
    image_path: str,
    max_size: int,
    min_quality: int = 30,
    min_scale: float = 0.3,
    prefer_webp: bool = False,
) -> tuple:
    """Compress ``image_path`` to fit within ``max_size`` bytes using libvips.

    The source image is never fully materialized in Python memory: only header
    metadata is read up front, and each candidate is produced by a streaming
    ``thumbnail`` pipeline written directly to a temporary file.

    Returns ``(image_path, False)`` untouched when the file already fits, or
    ``(output_temp_path, True)`` when compression produced a new file.  Raises
    :class:`~telepress.exceptions.ConversionError` when the image cannot be
    decoded/encoded or cannot be squeezed under ``max_size``.
    """
    file_size = os.path.getsize(image_path)
    if file_size <= max_size:
        return image_path, False

    ext = os.path.splitext(image_path)[1].lower()
    if ext in SKIP_COMPRESSION_FORMATS:
        raise ConversionError(
            f"Cannot auto-compress {ext.upper()} files (may be animated). "
            f"File size: {file_size / 1024 / 1024:.2f}MB, "
            f"max: {max_size / 1024 / 1024:.0f}MB"
        )

    out_format, _ = _output_format(prefer_webp)
    created = []
    accepted = None
    width = height = 0
    try:
        # Read only the header metadata; do not materialize full pixels.
        info = pyvips.Image.new_from_file(image_path, access='sequential')
        width, height = info.width, info.height
        info = None

        base_edge = _safe_edge(width, height)
        edges = [base_edge]
        scale = 0.9
        while scale >= min_scale - 1e-9:
            edges.append(max(1, int(base_edge * scale)))
            scale -= 0.1

        for edge in edges:
            accepted = _search_at_edge(
                image_path, edge, out_format, max_size, min_quality, created)
            if accepted is not None:
                return accepted, True

        raise ConversionError(
            f"Unable to compress image to under {max_size / 1024 / 1024:.0f}MB. "
            f"Original: {file_size / 1024 / 1024:.2f}MB, "
            f"dimensions: {width}x{height}"
        )
    except ConversionError:
        raise
    except Exception as e:  # noqa: BLE001 - surface any libvips failure
        raise ConversionError(f"Failed to compress image: {e}") from e
    finally:
        # Remove every candidate except the file that was accepted and returned.
        for path in created:
            if accepted is not None and path == accepted:
                continue
            _unlink_quiet(path)