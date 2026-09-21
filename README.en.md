# TelePress

[![CI](https://github.com/redtidev1918/TelePress/actions/workflows/ci.yml/badge.svg)](https://github.com/redtidev1918/TelePress/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/telepress.svg)](https://pypi.org/project/telepress/)
[![Python](https://img.shields.io/pypi/pyversions/telepress.svg)](https://pypi.org/project/telepress/)
[![Docs](https://img.shields.io/badge/Docs-documentation-6366f1?style=flat-square)](https://redtidev1918.github.io/TelePress/)

**Language / 语言:** English · [中文](README.md)

**A Python library and CLI that publishes text, images and archives to Telegraph.**

📖 [Full documentation](https://redtidev1918.github.io/TelePress/)

TelePress is a publishing plane: it turns Markdown, plain text, images and rich
media into Telegraph pages, regardless of which platform the content came from.

- Plain text / Markdown: automatic pagination with Prev / Next navigation
- Images / ZIP galleries: compressed and published as a Telegra.ph album
- Rich media (REST): publish Markdown + local images via `/publish/rich-novel`
- Images can be resolved through an **upload host** or a **generic CDN proxy**

## Install

```bash
pip install telepress

# Optional: REST API server
pip install "telepress[api]"

# Optional: S3 / R2 / OSS / MinIO compatible hosts
pip install "telepress[s3]"

# Optional: YAML config
pip install "telepress[yaml]"
```

## 30-second quick start

```bash
pip install telepress
telepress article.md --title "My article"

# Or the explicit subcommand
telepress publish article.md --title "My article"
```

Before publishing images / ZIP galleries, configure one image host:

```bash
telepress configure
telepress check
telepress photo.jpg --title "Photo"
telepress gallery.zip --title "Gallery"
```

To run the server:

```bash
pip install "telepress[api]"
telepress-server --host 127.0.0.1 --port 8000
# Interactive OpenAPI docs: http://127.0.0.1:8000/docs
```

On first use TelePress creates and stores a Telegraph token automatically
(`~/.telegraph_token` by default).

## Documentation

The README is not a full manual; the stable contracts live under `docs/`:

- Getting started / config: [getting-started.md](/docs/en/getting-started.md) · [configuration.md](/docs/en/configuration.md)
- REST API: [docs/en/api/README.md](/docs/en/api/README.md)
- Media: [docs/en/media/README.md](/docs/en/media/README.md)
- Python API / CLI: [python-api.md](/docs/en/python-api.md) · [cli.md](/docs/en/cli.md)
- Architecture: [publishing-plane.md](/docs/en/architecture/publishing-plane.md)
- Operations / current state: [current-state.md](/docs/en/operations/current-state.md)

## License

[MIT](LICENSE)

## Acknowledgements

TelePress builds on:

- [Python-Markdown](https://python-markdown.github.io/): Markdown parsing and extensions.
- [Pillow](https://github.com/python-pillow/Pillow): gallery compression.
- [requests](https://github.com/psf/requests): HTTP client.
- [telegraph](https://github.com/python-telegram-bot/telegraph) (the python-telegram-bot team's Telegraph wrapper): publishing pages.
- Optional REST layer: [FastAPI](https://fastapi.tiangolo.com/) · [Uvicorn](https://www.uvicorn.org/).

Interfaces: [Telegraph API](https://telegra.ph/api).
