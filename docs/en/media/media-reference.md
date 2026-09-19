# MediaReference

**Language / 语言:** English · [中文](../../media/media-reference.md)

`MediaReference` is the unified media-resolution concept.

## Core fields

| Field | Description |
| --- | --- |
| `local_ref` / `local` | Local relative path referenced by Markdown |
| `source_url` / `sourceUrl` | Original CDN / upstream URL |
| `asset_id` / `assetId` | Optional stable caller-side asset id |
| `local_path` / `localPath` | Optional extended local-path field |

## JSON shapes

Rich-novel manifests accept both legacy and new forms:

```json
[{"local": "images/001.jpg", "source": "https://cdn.example.com/full/001.jpg"}]
```

```json
[{"local": "images/001.jpg", "sourceUrl": "https://cdn.example.com/full/001.jpg", "assetId": "a-1"}]
```

Gallery remote media uses a separate shape:

```json
[{"assetId": "a", "kind": "image", "sourceUrl": "https://cdn.example.com/full/001.jpg", "filename": "001.jpg"}]
```

## Resolution

```text
MediaReference
      │
      ├── https + host allowlisted → proxied
      │
      └── other → ImageHost upload (uploaded / failed)
```
