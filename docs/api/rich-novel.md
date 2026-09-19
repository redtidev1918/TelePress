# POST /publish/rich-novel

**Language / 语言:** [中文](rich-novel.md) · [English](../en/api/rich-novel.md)

## 用途

发布富媒体小说：一个 Markdown 文件 + 重复的本地图片字段（`images`），
图片引用来改写为远端 URL 后按源顺序渲染并发布。

## 请求 Content-Type

`multipart/form-data`

## 字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `md` | file | 是 | Markdown，用相对路径引用本地图，如 `![](images/001.jpg)` |
| `images` | file（可重复） | 否 | 每个 multipart 文件名必须与 md 引用路径一致（如 `images/001.jpg`） |
| `title` | string | 否 | 页面标题，缺省 `Novel` |
| `token` | string | 否 | 显式 Telegraph token |
| `manifest` | string | 否 | JSON 数组，见下 |

## manifest（可选）

```json
[{"local":"images/001.jpg","source":"https://cdn.example.com/full/001.jpg","assetId":"a-1"}]
```

媒体解析规则：

- 命中「通用 CDN 代理」允许列表 → 改写成 proxy URL，`status=proxied`
- 其他来源 → 走图床上传，`status=uploaded` 或 `status=failed`
- 失败不致命：页面仍会发布（不会摧毁纯文本路径）

## asset 状态

| 状态 | 含义 |
| --- | --- |
| `uploaded` | 本地图上传统一图床成功 |
| `proxied` | 命中允许列表，改写到媒体代理 |
| `failed` | 上传失败，保留原引用，页面仍可发布 |

## 返回模型

```json
{
  "url": "https://telegra.ph/Novel-09-20",
  "status": "success",
  "assets": [
    {"local": "images/001.jpg", "remote": "https://...", "status": "proxied", "assetId": "a-1"}
  ]
}
```

## 完整示例

```bash
curl -X POST http://127.0.0.1:8000/publish/rich-novel \
  -F "md=@novel.md" \
  -F "images=@images/001.jpg" \
  -F "images=@images/002.jpg" \
  -F "title=富媒体小说" \
  -F 'manifest=[{"local":"images/001.jpg","source":"https://cdn.example.com/full/001.jpg"}]'
```
