# POST /publish/text

**Language / 语言:** English · [中文](../../api/text.md)

## Purpose

Publish a string of Markdown / plain text to a Telegraph page.

## Content-Type

`application/json`

## Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `content` | string | yes | Markdown or plain text |
| `title` | string | yes | Page title |
| `token` | string | no | Explicit Telegraph token |

## Response

```json
{ "url": "https://telegra.ph/Example-09-20", "status": "success" }
```

## Example

```bash
curl -X POST http://127.0.0.1:8000/publish/text \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{"content":"# Heading\n\nBody","title":"Example"}'
```
