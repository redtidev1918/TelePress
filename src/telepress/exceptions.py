class TelePressError(Exception):
    """Base exception for TelePress."""
    pass

class DependencyError(TelePressError):
    """Raised when required dependencies are missing."""
    pass

class AuthenticationError(TelePressError):
    """Raised when authentication fails."""
    pass

class ConversionError(TelePressError):
    """Raised when file conversion fails."""
    pass

class UploadError(TelePressError):
    """Raised when file upload fails."""
    pass

class SecurityError(TelePressError):
    """Raised when a security violation is detected (e.g. Zip Slip, huge file)."""
    pass

class ValidationError(TelePressError):
    """Raised when input data validation fails (e.g. invalid format, limits exceeded)."""
    pass


class RetryableError(UploadError):
    """Transient failure that is safe to retry (network hiccup, temporary HTTP 5xx).

    Subclasses of :class:`UploadError` so existing ``except UploadError``
    handlers keep working unchanged.
    """

class RateLimitError(RetryableError):
    """The upstream rate-limited us (HTTP 429, Telegraph flood control, etc.).

    May carry an optional ``retry_after`` (seconds) so callers can honor
    ``Retry-After`` when the upstream provides one.
    """

    def __init__(self, message="Rate limited", retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


class ProviderAuthError(UploadError):
    """Permanent credential failure (bad API key / token / 401/403 auth)."""

class ProviderPermanentError(UploadError):
    """Permanent, non-retryable provider failure (malformed response, 4xx)."""
