# Python API

**Language / 语言:** English · [中文](../python-api.md)

## Publish

```python
from telepress import TelegraphPublisher, publish, publish_text

url = publish("article.md", title="My article")
text_url = publish_text("# Heading\n\nBody", title="Example")

publisher = TelegraphPublisher(image_size_limit=10)
gallery_url = publisher.publish("gallery.zip", title="Gallery")
```

## Upload images

```python
from telepress import ImageUploader

uploader = ImageUploader("imgbb", api_key="your-key")
url = uploader.upload("photo.jpg")

batch = uploader.upload_batch(["1.jpg", "2.jpg"])
print(batch.success_rate, batch.get_url_map())
```

`ImageUploader()` with no arguments loads config from `~/.telepress.json` / env.

### Structured media result (ResolvedMedia)

`resolve()` is the structured counterpart of `upload()`: **`upload()` still returns
a `str` URL (backwards compatible)**, while the new `resolve()` returns a
`ResolvedMedia` carrying provider-qualified metadata:

```python
from telepress.media_result import ResolvedMedia, provider_qualify

m = uploader.resolve("photo.jpg", mime_type="image/jpeg")
# ResolvedMedia(url=..., media_id=..., provider=..., mime_type=...)
print(m.url, m.media_id, m.media_uri)   # media_uri: "catbox://abc123"

# Old UploadResult can be upgraded via as_resolved(); fields stay backwards compatible
result = uploader.upload_safe("photo.jpg")
if result.success:
    m = result.as_resolved()
```

- `ResolvedMedia.url` is always a plain usable string — it never breaks `url = resolve(...)`.
- `media_uri` (`provider://media_id`) stops a bare media id from floating free of its
  provider, so identity survives migrating from Provider A to Provider B.
- `provider_qualify(provider, media_id)` is a standalone helper.

## Exports

The `telepress` package exports publishers, uploaders, host classes
(`ImgbbHost`, `ImgurHost`, `SmmsHost`, `CatboxHost`, `FreeImageHost`,
`UploadcareHost`, `ImageKitHost`, `CloudinaryHost`, `ZeroXZeroHost`,
`LitterboxHost`, `R2Host`, `S3Host`, `CustomHost`), `ResolvedMedia`,
`create_image_host`, `load_config`, `get_image_host_config`,
`provider_qualify`, exceptions (`TelePressError`,
`ValidationError`, `UploadError`, `AuthenticationError`, `SecurityError`,
`DependencyError`, `ConversionError`, `RetryableError`, `RateLimitError`,
`ProviderAuthError`, `ProviderPermanentError`), constants and utilities.

## Errors

```python
from telepress import TelePressError, ValidationError, publish

try:
    url = publish("article.md")
except ValidationError as exc:
    print(f"Invalid input: {exc}")
except TelePressError as exc:
    print(f"Publish failed: {exc}")
```

The error hierarchy lets callers decide whether to retry:

- `UploadError` — base class; `except UploadError` still catches all upload errors.
- `RetryableError` — transient (timeout, connection reset, 5xx); **retryable**.
- `RateLimitError` — rate limited / 429; **retryable**, honoring `retry_after`.
- `ProviderAuthError` — auth failure (invalid API key, etc.); **do not retry**.
- `ProviderPermanentError` — permanent (permissions, invalid input, unsupported media);
  **do not retry**.

`_upload_with_retry` applies this classification: permanent errors fail fast,
retryable errors get exponential backoff. Every new exception inherits from
`UploadError`, so existing `except UploadError` code needs no changes.
