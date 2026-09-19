# POST /publish/text

**Language / 语言:** [中文](text.md) · [English](../en/api/text.md)

## 用途

直接把 Markdown / 纯文本字符串发布为 Telegraph 页面。

## 请求 Content-Type

`application/json`

## 字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `content` | string | 是 | Markdown 或纯文本内容 |
| `title` | string | 是 | 页面标题 |
| `token` | string | 否 | 显式 Telegraph token |

## 返回模型

```json
{ "url": "https://telegra.ph/Example-09-20", "status": "success" }
```

## 完整示例

```bash
curl -X POST http://127.0.0.1:8000/publish/text \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{"content":"# 标题\n\n正文","title":"示例"}'
```
