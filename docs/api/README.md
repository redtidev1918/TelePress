# REST API

**Language / 语言:** [中文](README.md) · [English](../en/api/README.md)

启动服务：

```bash
pip install "telepress[api]"
telepress-server --host 127.0.0.1 --port 8000
```

OpenAPI 交互文档：`http://127.0.0.1:8000/docs`。

## 请求级鉴权

设置 `TELEPRESS_API_KEY` 后，`/publish/*` 需要以下任一请求头：

- `Authorization: Bearer <key>`
- `X-TelePress-Key: <key>`

未设置 key 时保持开放（开发/本地场景）。**请勿把无鉴权的发布接口直接暴露公网。**

## 端点一览

| 端点 | 方法 | 请求体 | 返回 |
| --- | --- | --- | --- |
| `/publish/text` | POST | JSON `{content, title, token?}` | `{url, status}` |
| `/publish/file` | POST | multipart `file`, `title?`, `token?` | `{url, status}` |
| `/publish/gallery` | POST | multipart `files*`, 可选 `title/tags/link/spoiler/token/media` | `{url, ok, files}` |
| `/publish/rich-novel` | POST | multipart `md`, `images*?`, `title?`, `token?`, `manifest?` | `{url, assets[]}` |

## 失败语义

- `400`：TelePress 或 Validation 错误（例如 media JSON 解析失败、超过 50 MiB 上限）
- `401`：API key 缺失 / 不匹配
- `422`：缺少必要字段（例如 gallery 没有 files 也没有 media）
- `500`：未预期内部错误

文件读写、图片压缩和同步网络请求在线程池执行，不会阻塞 API 事件循环。

## 文档

- [text.md](text.md)
- [file.md](file.md)
- [gallery.md](gallery.md)
- [rich-novel.md](rich-novel.md)
