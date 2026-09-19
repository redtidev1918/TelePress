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

## Exports

The `telepress` package exports publishers, uploaders, host classes
(`ImgbbHost`, `ImgurHost`, `SmmsHost`, `CatboxHost`, `FreeImageHost`,
`UploadcareHost`, `ImageKitHost`, `CloudinaryHost`, `ZeroXZeroHost`,
`LitterboxHost`, `R2Host`, `S3Host`, `CustomHost`), `create_image_host`,
`load_config`, `get_image_host_config`, exceptions (`TelePressError`,
`ValidationError`, `UploadError`, `AuthenticationError`, `SecurityError`,
`DependencyError`, `ConversionError`), constants and utilities.

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
