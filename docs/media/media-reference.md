# MediaReference

**Language / 语言:** [中文](media-reference.md) · [English](../en/media/media-reference.md)

`MediaReference` 是媒体解析的统一概念。它描述「一份媒体应该从哪来、回传到哪里」。

## 核心字段

| 字段 | 说明 |
| --- | --- |
| `local_ref` / `local` | Markdown 里的本地相对路径 |
| `source_url` / `sourceUrl` | 原始 CDN / 上游 URL |
| `asset_id` / `assetId` | 调用方侧资产的稳定 ID（可选） |
| `local_path` / `localPath` | 与本地路径相关的扩展字段（可选） |

## JSON 形态

rich-novel manifest 同时接受两种写法：

```json
[{"local": "images/001.jpg", "source": "https://cdn.example.com/full/001.jpg"}]
```

```json
[{"local": "images/001.jpg", "sourceUrl": "https://cdn.example.com/full/001.jpg", "assetId": "a-1"}]
```

gallery 的远程 media 使用独立形态：

```json
[{"assetId": "a", "kind": "image", "sourceUrl": "https://cdn.example.com/full/001.jpg", "filename": "001.jpg"}]
```

## 解析规则

```text
MediaReference
      │
      ├── https + host 在 proxy allowlist → proxied
      │
      └── 其他 → ImageHost 上传（uploaded / failed）
```
