# POST /publish/gallery

**Language / 语言:** [中文](gallery.md) · [English](../en/api/gallery.md)

## 用途

把多张图片发布为 Telegra.ph 相册：

- 默认路径：重复 `files` multipart 字段
- 可选路径：`media` JSON manifest（远程抓取，默认关闭）

## 请求 Content-Type

`multipart/form-data`

## 字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `files` | file（可重复） | 否（media 存在时可不传） | 按上传顺序打包成 zip |
| `title` | string | 否 | 标题，缺省用第一个文件的文件名 |
| `tags` | string | 否 | 逗号分隔，渲染在首页页脚 |
| `link` | string | 否 | 来源链接，渲染在首页页脚 |
| `spoiler` | truthy | 否 | 成人/剧透提示（`1` / `true` / `yes` / `on`） |
| `token` | string | 否 | 显式 Telegraph token |
| `media` | string | 否 | JSON 数组（需开启远程 manifest） |

## 默认路径（稳定契约）

`files` 是稳定、默认路径。文件按上传顺序打包成 zip，自动分页并显示
「上一页/下一页」。

## 远程 media manifest（opt-in）

默认关闭。需服务端设置：

```bash
export TELEPRESS_ALLOW_REMOTE_GALLERY_MEDIA=1
```

`media` JSON 数组格式：

```json
[{"assetId":"a","kind":"image","sourceUrl":"https://cdn.example.com/full/001.jpg","filename":"001.jpg"}]
```

约束：

- `sourceUrl` 只接受 `https://`
- 单文件上限 50 MiB
- 未开启或抓取失败都不影响原有 multipart 路径

## 返回模型

```json
{ "url": "https://telegra.ph/Gallery-09-20", "status": "success", "ok": true, "files": 12 }
```

`files` 是实际计入相册的媒体数。

## 完整示例

```bash
# 默认 multipart
curl -X POST http://127.0.0.1:8000/publish/gallery \
  -F "files=@p0.jpg" \
  -F "files=@p1.jpg" \
  -F "title=相册标题" \
  -F "tags=artwork, illustration" \
  -F "link=https://example.com/artworks/123456" \
  -F "spoiler=true"

# 远程 media manifest
curl -X POST http://127.0.0.1:8000/publish/gallery \
  -F 'media=[{"assetId":"a","kind":"image","sourceUrl":"https://cdn.example.com/full/001.jpg","filename":"001.jpg"}]'
```
