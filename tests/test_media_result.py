"""Tests for the new structured ResolvedMedia result and provider-qualified id.

Covers:
  - ResolvedMedia fields + media_uri derivation
  - provider_qualify helper
  - UploadResult.as_resolved() upgrade path (backwards compatible)
  - resolve() entry point returns ResolvedMedia while upload() still returns str
  - backward compatibility: existing UploadResult fields unchanged
"""
import os
import tempfile
import unittest
from unittest.mock import patch

from telepress.media_result import ResolvedMedia, provider_qualify
from telepress.uploader import ImageUploader, UploadResult, BatchUploadResult
from telepress.image_host import ImageHost


class DummyHost(ImageHost):
    """Minimal upload host for resolve() tests (no compression)."""

    def __init__(self, url="http://mock/ok.jpg"):
        self._url = url
        self.calls = []

    @property
    def name(self):
        return "catbox"

    def upload(self, image_path):
        self.calls.append(image_path)
        return self._url


class TestResolvedMedia(unittest.TestCase):
    def test_fields_and_defaults(self):
        m = ResolvedMedia(url="http://x/1.jpg", provider="catbox", media_id="abc")
        self.assertEqual(m.url, "http://x/1.jpg")
        self.assertEqual(m.provider, "catbox")
        self.assertEqual(m.media_id, "abc")
        self.assertIsNone(m.mime_type)
        self.assertIsNone(m.filename)
        self.assertIsNone(m.size)
        self.assertEqual(m.metadata, {})

    def test_media_uri_qualified(self):
        m = ResolvedMedia(url="http://x/1", provider="r2", media_id="123")
        self.assertEqual(m.media_uri, "r2://123")

    def test_media_uri_none_when_id_missing(self):
        m = ResolvedMedia(url="http://x/1", provider="catbox", media_id=None)
        self.assertIsNone(m.media_uri)

    def test_media_uri_none_when_provider_missing(self):
        m = ResolvedMedia(url="http://x/1", provider=None, media_id="123")
        self.assertIsNone(m.media_uri)

    def test_metadata_is_independent_per_instance(self):
        a = ResolvedMedia(url="http://x/1", metadata={"k": "a"})
        b = ResolvedMedia(url="http://x/2")
        self.assertEqual(a.metadata, {"k": "a"})
        self.assertNotEqual(a.metadata, b.metadata)


class TestProviderQualify(unittest.TestCase):
    def test_both_present(self):
        self.assertEqual(provider_qualify("s3", "obj"), "s3://obj")

    def test_missing_provider(self):
        self.assertIsNone(provider_qualify(None, "obj"))

    def test_missing_id(self):
        self.assertIsNone(provider_qualify("s3", None))


class TestUploadResultUpgrade(unittest.TestCase):
    def test_as_resolved_preserves_url_and_provider(self):
        r = UploadResult(
            path="/tmp/a.jpg", url="http://x/a.jpg", success=True,
            provider="r2", media_id="key",
        )
        m = r.as_resolved()
        self.assertIsInstance(m, ResolvedMedia)
        self.assertEqual(m.url, "http://x/a.jpg")
        self.assertEqual(m.provider, "r2")
        self.assertEqual(m.media_uri, "r2://key")

    def test_existing_fields_backwards_compatible(self):
        # Old call: only path/url/success — new fields must all be optional.
        r = UploadResult(path="/tmp/a.jpg", url="http://x/a.jpg", success=True)
        self.assertTrue(r.success)
        self.assertEqual(r.url, "http://x/a.jpg")
        # New fields default to None (no break for old readers).
        self.assertIsNone(r.provider)
        self.assertIsNone(r.media_id)
        self.assertIsNone(r.media_uri)


class TestResolveEntryPoint(unittest.TestCase):
    def test_resolve_returns_resolved_media(self):
        host = DummyHost()
        uploader = ImageUploader(host=host)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.close()
            try:
                with patch("telepress.uploader.compress_image_to_size",
                           return_value=(f.name, False)):
                    m = uploader.resolve(f.name, mime_type="image/jpeg")
                self.assertIsInstance(m, ResolvedMedia)
                self.assertEqual(m.url, "http://mock/ok.jpg")
                self.assertEqual(m.provider, "catbox")
                self.assertEqual(m.mime_type, "image/jpeg")
                self.assertEqual(m.filename, os.path.basename(f.name))
                self.assertIsNotNone(m.size)
                self.assertEqual(m.source_id, f.name)
            finally:
                if os.path.exists(f.name):
                    os.unlink(f.name)

    def test_upload_still_returns_str(self):
        host = DummyHost()
        uploader = ImageUploader(host=host)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.close()
            try:
                with patch("telepress.uploader.compress_image_to_size",
                           return_value=(f.name, False)):
                    url = uploader.upload(f.name)
                self.assertIsInstance(url, str)  # unchanged contract
                self.assertEqual(url, "http://mock/ok.jpg")
            finally:
                if os.path.exists(f.name):
                    os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()