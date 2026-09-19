# POST /publish/rich-novel

**Language / 语言:** English · [中文](../../api/rich-novel.md)

## Purpose

Publish a rich novel: one Markdown file plus repeated local `images` parts.
Local image refs are rewritten to remote URLs, DOM nodes are rendered in
source order and the page is published.

## Content-Type

`multipart/form-data`

## Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `md` | file | yes | Markdown referencing local images, e.g. `![](images/001.jpg)` |
| `images` | file (repeatable) | no | filenames must match markdown refs (`images/001.jpg`) |
| `title` | string | no | page title, default `Novel` |
| `token` | string | no | explicit Telegraph token |
| `manifest` | string | no | JSON array (see below) |

## Optional manifest

```json
[{"local":"images/001.jpg","source":"https://cdn.example.com/full/001.jpg","assetId":"a-1"}]
```

Media resolution:

- allowlisted https + proxy configured → rewritten proxy URL, `status=proxied`
- otherwise → image-host upload, `status=uploaded` or `status=failed`
- failures are non-fatal: the page still publishes

## Asset statuses

| Status | Meaning |
| --- | --- |
| `uploaded` | uploaded to the configured image host |
| `proxied` | rewritten through the allowlisted media proxy |
| `failed` | upload failed; original ref kept, page still publishes |

## Response

```json
{
  "url": "https://telegra.ph/Novel-09-20",
  "status": "success",
  "assets": [
    {"local": "images/001.jpg", "remote": "https://...", "status": "proxied", "assetId": "a-1"}
  ]
}
```

## Example

```bash
curl -X POST http://127.0.0.1:8000/publish/rich-novel \
  -F "md=@novel.md" \
  -F "images=@images/001.jpg" \
  -F "images=@images/002.jpg" \
  -F "title=Rich Novel" \
  -F 'manifest=[{"local":"images/001.jpg","source":"https://cdn.example.com/full/001.jpg"}]'
```
