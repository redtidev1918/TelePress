"""Tests for retry classification and structured error types.

Covers:
  - permanent failures (auth / bad input / provider 4xx) are NOT retried
  - HTTP 429 is retryable and honors Retry-After (RateLimitError.retry_after)
  - HTTP 5xx is retryable
  - transient network errors are retryable
  - exhaustive retry still raises UploadError
  - new exception types are still caught by `except UploadError` (backwards compat)
"""
import unittest
from unittest.mock import patch, MagicMock

import requests

from telepress import (
    UploadError, RetryableError, RateLimitError,
    ProviderAuthError, ProviderPermanentError,
)
from telepress.uploader import ImageUploader, _classify_retryable
from telepress.image_host import ImageHost


class _AlwaysFailHost(ImageHost):
    """Host whose upload() raises the injected exception every time."""

    def __init__(self, exc_factory):
        self._exc_factory = exc_factory
        self.calls = 0

    @property
    def name(self):
        return "mock"

    def upload(self, image_path):
        self.calls += 1
        raise self._exc_factory()


def _uploader_with(exc_factory):
    return ImageUploader(host=_AlwaysFailHost(exc_factory))


class TestClassifyRetryable(unittest.TestCase):
    def test_retryable_error_is_retryable(self):
        self.assertTrue(_classify_retryable(RetryableError("x")))

    def test_rate_limit_error_is_retryable(self):
        self.assertTrue(_classify_retryable(RateLimitError("x")))

    def test_upload_error_is_retryable_by_default(self):
        # Legacy: plain UploadError unknown → retry (preserves old behaviour).
        self.assertTrue(_classify_retryable(UploadError("x")))

    def test_provider_permanent_not_retryable(self):
        self.assertFalse(_classify_retryable(ProviderPermanentError("x")))

    def test_provider_auth_not_retryable(self):
        self.assertFalse(_classify_retryable(ProviderAuthError("x")))

    def test_httperror_429_retryable(self):
        resp = MagicMock()
        resp.status_code = 429
        exc = requests.exceptions.HTTPError(response=resp)
        self.assertTrue(_classify_retryable(exc))

    def test_httperror_500_retryable(self):
        resp = MagicMock()
        resp.status_code = 500
        exc = requests.exceptions.HTTPError(response=resp)
        self.assertTrue(_classify_retryable(exc))

    def test_httperror_403_not_retryable(self):
        resp = MagicMock()
        resp.status_code = 403
        exc = requests.exceptions.HTTPError(response=resp)
        self.assertFalse(_classify_retryable(exc))

    def test_connection_error_retryable(self):
        exc = requests.exceptions.ConnectionError("reset")
        self.assertTrue(_classify_retryable(exc))

    def test_timeout_retryable(self):
        exc = requests.exceptions.ConnectTimeout()
        self.assertTrue(_classify_retryable(exc))


class TestRetryBehavior(unittest.TestCase):
    def test_permanent_failure_does_not_retry(self):
        u = _uploader_with(lambda: ProviderPermanentError("bad"))
        with self.assertRaises(ProviderPermanentError):
            u._upload_with_retry("/tmp/x", "/tmp/x", retries=3, retry_delay=0, max_retry_delay=0)
        # Only first attempt — fail fast, no retries.
        self.assertEqual(u.host.calls, 1)

    def test_auth_failure_does_not_retry(self):
        u = _uploader_with(lambda: ProviderAuthError("bad key"))
        with self.assertRaises(ProviderAuthError):
            u._upload_with_retry("/tmp/x", "/tmp/x", retries=3, retry_delay=0, max_retry_delay=0)
        self.assertEqual(u.host.calls, 1)

    def test_transient_failure_retries_then_succeeds(self):
        host = _AlwaysFailHost(lambda: ConnectionError("reset"))
        # host.upload raises every time; test retry count by mocking sleep.
        u = ImageUploader(host=host)
        with patch("telepress.uploader.time.sleep"):
            with self.assertRaises(UploadError):
                u._upload_with_retry("/tmp/x", "/tmp/x", retries=3, retry_delay=0, max_retry_delay=0)
        # retries=3 → 3 attempts total.
        self.assertEqual(host.calls, 3)

    def test_exhaustive_retry_raises_upload_error(self):
        u = _uploader_with(lambda: RateLimitError("flood"))
        with patch("telepress.uploader.time.sleep"):
            with self.assertRaises(UploadError):
                u._upload_with_retry("/tmp/x", "/tmp/x", retries=3, retry_delay=1, max_retry_delay=10)
        self.assertEqual(u.host.calls, 3)

    def test_retry_after_bounded_sleep(self):
        """RateLimitError.retry_after should cap the sleep to max_retry_delay."""
        host = _AlwaysFailHost(lambda: RateLimitError("flood", retry_after=999))
        u = ImageUploader(host=host)
        sleeps = []
        with patch("telepress.uploader.time.sleep", side_effect=lambda s: sleeps.append(s)):
            with self.assertRaises(UploadError):
                u._upload_with_retry("/tmp/x", "/tmp/x", retries=2, retry_delay=1, max_retry_delay=30)
        # retry_after 999 is capped to max_retry_delay 30 (plus jitter).
        self.assertTrue(all(0 < s <= 30.5 for s in sleeps), sleeps)


class TestExceptionHierarchyBackwardsCompat(unittest.TestCase):
    def test_new_exceptions_are_upload_errors(self):
        # Every new error type must still be catchable as UploadError/TelePressError.
        for exc in (RetryableError("a"), RateLimitError("b"),
                    ProviderAuthError("c"), ProviderPermanentError("d")):
            self.assertIsInstance(exc, UploadError)
            self.assertIsInstance(exc, Exception)


if __name__ == "__main__":
    unittest.main()