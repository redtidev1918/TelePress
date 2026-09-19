# REST API

**Language / 语言:** English · [中文](../../api/README.md)

```bash
pip install "telepress[api]"
telepress-server --host 127.0.0.1 --port 8000
```

Interactive OpenAPI docs: `http://127.0.0.1:8000/docs`.

## Auth

When `TELEPRESS_API_KEY` is set, `/publish/*` requires one of:

- `Authorization: Bearer <key>`
- `X-TelePress-Key: <key>`

Never expose a key-less publish endpoint to the public internet.

## Endpoints

| Endpoint | Method | Body | Response |
| --- | --- | --- | --- |
| `/publish/text` | POST | JSON `{content, title, token?}` | `{url, status}` |
| `/publish/file` | POST | multipart `file`, `title?`, `token?` | `{url, status}` |
| `/publish/gallery` | POST | repeated `files*`, optional `title/tags/link/spoiler/token/media` | `{url, ok, files}` |
| `/publish/rich-novel` | POST | multipart `md`, `images*?`, `title?`, `token?`, `manifest?` | `{url, assets[]}` |

## Failure semantics

- `400`: TelePress / validation error (bad media JSON, >50 MiB, etc.)
- `401`: missing / wrong API key
- `422`: missing required fields
- `500`: unexpected internal error

Blocking file, compression, and network work runs in a thread pool.

## Docs

- [text.md](text.md)
- [file.md](file.md)
- [gallery.md](gallery.md)
- [rich-novel.md](rich-novel.md)
