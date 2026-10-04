# POST /publish/file

**Language / 语言:** English · [中文](../../api/file.md)

## Purpose

Upload one file (markdown / txt / zip / image) and publish it.

## Content-Type

`multipart/form-data`

## Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `file` | file | yes | File to publish |
| `title` | string | no | Title; defaults to filename |
| `token` | string | no | Explicit Telegraph token |
| `author_name` | string | no | Author name displayed below the page title |
| `author_url` | string | no | `http`/`https` URL opened when the author name is clicked |

## Response

```json
{ "url": "https://telegra.ph/Example-09-20", "status": "success" }
```

## Example

```bash
curl -X POST http://127.0.0.1:8000/publish/file \
  -F "file=@article.md" \
  -F "title=Example" \
  -F "author_name=Alice" \
  -F "author_url=https://example.com/alice"
```
