# POST /publish/file

**Language / 语言:** [中文](file.md) · [English](../en/api/file.md)

## 用途

上传一个文件（markdown / txt / zip / 图片）并发布。

## 请求 Content-Type

`multipart/form-data`

## 字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `file` | file | 是 | 要发布的文件 |
| `title` | string | 否 | 标题；缺省用上传文件名 |
| `token` | string | 否 | 显式 Telegraph token |

## 返回模型

```json
{ "url": "https://telegra.ph/Example-09-20", "status": "success" }
```

## 完整示例

```bash
curl -X POST http://127.0.0.1:8000/publish/file \
  -F "file=@article.md" \
  -F "title=示例"
```
