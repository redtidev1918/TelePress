# POST /publish/gallery

**Language / 语言:** English · [中文](../../api/gallery.md)

## Purpose

Publish multiple images as a Telegra.ph album:

- **Default path**: repeated `files` multipart parts
- **Optional path**: `media` JSON manifest (remote fetch, disabled by default)

## Content-Type

`multipart/form-data`

## Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `files` | file (repeatable) | no (media may be present) | packed into a zip in order |
| `title` | string | no | defaults to the first file name |
| `tags` | string | no | comma-separated, rendered in the footer |
| `link` | string | no | source link, rendered in the footer |
| `spoiler` | truthy | no | adult/spoiler marker (`1` / `true` / `yes` / `on`) |
| `token` | string | no | explicit Telegraph token |
| `media` | string | no | JSON array (requires remote manifest) |

## Default path (stable contract)

`files` is the stable default. Files are packed into a zip in upload order and
published with automatic pagination and Prev / Next navigation.

## Optional remote manifest

Disabled by default. Enable on the server:

```bash
export TELEPRESS_ALLOW_REMOTE_GALLERY_MEDIA=1
```

`media` JSON:

```json
[{"assetId":"a","kind":"image","sourceUrl":"https://cdn.example.com/full/001.jpg","filename":"001.jpg"}]
```

Constraints:

- `sourceUrl` must be `https://`
- 50 MiB cap per file
- A missing flag or a fetch failure never affects the `files` path

## Response

```json
{ "url": "https://telegra.ph/Gallery-09-20", "status": "success", "ok": true, "files": 12 }
```

## Examples

```bash
curl -X POST http://127.0.0.1:8000/publish/gallery \
  -F "files=@p0.jpg" \
  -F "files=@p1.jpg" \
  -F "title=Album" \
  -F "tags=artwork, illustration" \
  -F "link=https://example.com/artworks/123456" \
  -F "spoiler=true"

curl -X POST http://127.0.0.1:8000/publish/gallery \
  -F 'media=[{"assetId":"a","kind":"image","sourceUrl":"https://cdn.example.com/full/001.jpg","filename":"001.jpg"}]'
```
