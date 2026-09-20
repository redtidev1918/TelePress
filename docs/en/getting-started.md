# Getting Started

**Language / 语言:** English · [中文](../getting-started.md)

## Requirements

- Python 3.10 or newer
- Telegraph token (created automatically on first use and stored in `~/.telegraph_token`)
- An image host only when publishing images / galleries

## Install

```bash
pip install telepress

# Optional: REST API
pip install "telepress[api]"

# Optional: S3 / R2 / OSS / MinIO compatible hosts
pip install "telepress[s3]"

# Optional: YAML config
pip install "telepress[yaml]"
```

Development install:

```bash
git clone https://github.com/redtidev1918/TelePress.git
cd telepress
python -m pip install --editable ".[dev]"
```

## 30-second run

```bash
telepress article.md --title "My article"

# Same as:
telepress publish article.md --title "My article"
```

Configure an image host before publishing images / ZIP galleries:

```bash
telepress configure
telepress check
telepress photo.jpg --title "Photo"
telepress gallery.zip --title "Gallery"
```

Common options:

```bash
telepress gallery.zip --image-size-limit 10
telepress gallery.zip --no-compress
telepress article.md --api-url http://localhost:9009
```

Plain-text publishing does not load or require image-host configuration.

## Server

```bash
pip install "telepress[api]"
telepress-server --host 127.0.0.1 --port 8000
```

Interactive OpenAPI docs are at `http://127.0.0.1:8000/docs`. See
[api/README.md](api/README.md).

## Behavior and limits

- Markdown / text are converted to Telegraph DOM nodes.
- Plain-text chapter headings such as `Chapter 1` / `第一章` are recognized.
- Large text is paginated around ~10,000 characters with Prev / Next navigation.
- Galleries paginate every 100 images.
- Default per-image limit is 5 MiB; oversized images are compressed (GIFs are not).
- Inputs are capped at 2 GiB before processing.
- `~/.telepress_cache.json` avoids re-publishing identical text.
- Supported extensions: `.txt`, `.md`, `.markdown`, `.rst`, `.text`, `.jpg`,
  `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`, `.zip`.
