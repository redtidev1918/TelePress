# TelePress

[![CI](https://github.com/redtidev1918/telepress/actions/workflows/ci.yml/badge.svg)](https://github.com/redtidev1918/telepress/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/telepress.svg)](https://pypi.org/project/telepress/)
[![Python](https://img.shields.io/pypi/pyversions/telepress.svg)](https://pypi.org/project/telepress/)

**语言 / Language:** 中文 · [English](README.en.md)

TelePress 用于把 Markdown、纯文本、图片和 ZIP 图集发布到
[Telegraph](https://telegra.ph)，支持自动分页、外部图床、图片压缩、并发上传和可选的 REST API。

## 环境要求

- Python 3.10 或更高版本
- Telegraph token；首次使用时也可以自动创建
- 只有发布图片或图集时才需要配置图床

## 安装

```bash
pip install telepress

# 可选：REST API
pip install "telepress[api]"

# 可选：AWS S3、Cloudflare R2 等 S3 兼容图床
pip install "telepress[s3]"

# 可选：YAML 配置文件
pip install "telepress[yaml]"
```

从源码安装开发环境：

```bash
git clone https://github.com/redtidev1918/telepress.git
cd telepress
python -m pip install --editable ".[dev]"
```

## 快速开始

发布文档：

```bash
telepress article.md --title "我的文章"

# 显式子命令写法与上面等价
telepress publish article.md --title "我的文章"
```

配置图床后发布图片或 ZIP 图集：

```bash
telepress configure
telepress check
telepress photo.jpg --title "照片"
telepress gallery.zip --title "图集"
```

常用参数：

```bash
# 临时覆盖图片大小限制，单位 MiB
telepress gallery.zip --image-size-limit 10

# 不压缩超限图片
telepress gallery.zip --no-compress

# 使用兼容 Telegraph 的自定义 API
telepress article.md --api-url http://localhost:9009
```

纯文本发布不会加载或要求图床配置。Telegraph token 会在需要时自动创建并保存到
`~/.telegraph_token`，也可以用 `--token` 显式传入。

## REST API

使用前先安装可选 API 依赖：`pip install "telepress[api]"`。

```bash
telepress-server --host 127.0.0.1 --port 8000
```

OpenAPI 交互文档位于 `http://127.0.0.1:8000/docs`。

```bash
curl -X POST http://127.0.0.1:8000/publish/text \
  -H "Content-Type: application/json" \
  -d '{"content":"# 标题\n\n正文","title":"示例"}'

curl -X POST http://127.0.0.1:8000/publish/file \
  -F "file=@article.md" \
  -F "title=示例"

curl -X POST http://127.0.0.1:8000/publish/gallery \
  -F "files=@p0.jpg" \
  -F "files=@p1.jpg" \
  -F "title=相册标题" \
  -F "tags=artwork, illustration" \
  -F "link=https://example.com/artworks/123456" \
  -F "spoiler=true"

curl -X POST http://127.0.0.1:8000/publish/rich-novel \
  -F "md=@novel.md" \
  -F "images=@images/001.jpg" \
  -F "images=@images/002.jpg" \
  -F "title=富媒体小说"
```

`/publish/gallery` 接收可重复的 `files` 文件字段，以及可选的 `title`、
`tags`（逗号分隔）、`link`（来源链接）和 `spoiler`（truthy 值即可，用于标记成人/剧透内容）
表单字段。文件按上传顺序打包成 zip 后发布为 Telegra.ph 相册，自动分页并
加上「上一页/下一页」导航；`tags`、`link` 和成人/剧透提示会渲染在首页页脚。
返回 `{"ok": true, "url": "...", "files": N}`，兼容任意把重复 `files`
multipart 字段投递到 `http://<telepress-host>:8000/publish/gallery` 的通用客户端。

`/publish/gallery` 的远程媒体 manifest 是**可选开关**：默认仍只接受重复 `files`
multipart（通用交付契约）。只有设置 `TELEPRESS_ALLOW_REMOTE_GALLERY_MEDIA=1` 并传入
`media` JSON 表单字段（`[{"assetId","kind","sourceUrl","filename"}]`）时，服务端
才会代为抓取 https 图源（单文件 50 MiB 上限）；未开启或抓取失败都不影响原有
multipart 路径。


`/publish/rich-novel` 接收一个 `md` 文件字段、可重复的 `images` 文件字段和可选
的 `title`。`md` 用相对路径引用本地图（例如 `![](images/001.jpg)`），每个
`images` 的 multipart 文件名必须与引用路径一致（例如 `images/001.jpg`）。图片
会先上传到配置的图床（如 Catbox），引用改写成远端 URL 后按源顺序渲染成
Telegraph 节点并发布。返回 `{"url": "...", "assets": [{"local", "remote",
"status"}], ...}`，`assets` 里每个本地图都能看到 `uploaded` / `failed` / `proxied`，
失败不致命、页面仍会发布。

可选 `manifest` 字段是一个 JSON 数组，例如：

```json
[{"local": "images/001.jpg", "source": "https://cdn.example.com/full/001.jpg"}]
```

以上 `manifest` 的代理改写是**通用 CDN 代理**，不再耦合 Pixiv：

- `TELEPRESS_MEDIA_PROXY_BASE`：代理入口 base URL（例如一个固定上游的媒体代理服务）。
- `TELEPRESS_MEDIA_PROXY_HOSTS`：允许改写的上游 CDN host 逗号列表（例如
  `cdn-a.example.com, cdn-b.example.com`）。只改写 host 在列表里的 `https` 条目，
  否则继续走图床上传 fallback，避免变成开放代理/SSRF。
- `TELEPRESS_MEDIA_PROXY_PATH_PREFIX`：可选路由前缀，默认 `media`；改写结果
  为 `<base>/<prefix>/<host>/<path>`。

兼容旧配置：只设置旧的 `TELEPRESS_PIXIV_PROXY_BASE` 时保持历史行为：放行旧白名单
`i.pximg.net` 并改写成 `<base>/pixiv/<path>`（仅作为向后兼容别名，不鼓励新配置）。

文件读写、图片压缩和同步网络请求会在线程池执行，不会阻塞 API 的异步事件循环。

## 图片托管

支持的图床：

- ImgBB、Imgur、sm.ms、Freeimage.host（图片）
- ImageKit、Cloudinary（图片 / CDN）
- Catbox（匿名或 userhash，任意文件）
- Uploadcare（public key，任意文件，CDN）
- 0x0.st、Litterbox（匿名临时文件，明确过期时间）
- AWS S3、Cloudflare R2、OSS、MinIO 等 S3 兼容存储
- Rclone remote
- 自定义 HTTP 上传 API

运行 `telepress configure` 可以交互式配置，也可以创建 `~/.telepress.json`：

```json
{
  "image_host": {
    "type": "rclone",
    "remote_path": "myremote:bucket/path",
    "public_url": "https://cdn.example.com/path",
    "rclone_flags": ["--transfers=32", "--checkers=32"],
    "max_size_mb": 20,
    "max_workers": 8
  }
}
```

S3 兼容配置：

```json
{
  "image_host": {
    "type": "s3",
    "access_key_id": "your-access-key",
    "secret_access_key": "your-secret-key",
    "bucket": "your-bucket",
    "public_url": "https://cdn.example.com",
    "endpoint_url": "https://s3.example.com",
    "region_name": "auto"
  }
}
```

Catbox 配置（支持匿名上传，不设置 `userhash` 即可）：

```bash
# 匿名上传
export TELEPRESS_IMAGE_HOST_TYPE=catbox

# 使用账号 userhash（可管理/匿名化文件）
export TELEPRESS_IMAGE_HOST_TYPE=catbox
export TELEPRESS_IMAGE_HOST_USERHASH=YOUR_USERHASH
```

```json
{
  "image_host": {
    "type": "catbox",
    "userhash": "YOUR_USERHASH"
  }
}
```

Catbox 本身不会替用户重新压缩文件。通过 `ImageUploader` 上传图片时，
TelePress 仍会按 `max_size` 先压缩；直接调用 `CatboxHost.upload(path)`
上，未绑定账号、无法在 Catbox 网页端管理或删除，请勿用来长期保存重要数据。

FreeImage.host：

```bash
export TELEPRESS_IMAGE_HOST_TYPE=freeimage
export TELEPRESS_IMAGE_HOST_API_KEY=YOUR_KEY
```

Uploadcare：

```bash
export TELEPRESS_IMAGE_HOST_TYPE=uploadcare
export TELEPRESS_IMAGE_HOST_PUBLIC_KEY=YOUR_PUBLIC_KEY
```

ImageKit：

```bash
export TELEPRESS_IMAGE_HOST_TYPE=imagekit
export TELEPRESS_IMAGE_HOST_PRIVATE_KEY=YOUR_PRIVATE_KEY
```

Cloudinary（unsigned preset）：

```bash
export TELEPRESS_IMAGE_HOST_TYPE=cloudinary
export TELEPRESS_IMAGE_HOST_CLOUD_NAME=your-cloud
export TELEPRESS_IMAGE_HOST_UPLOAD_PRESET=your-preset
```

临时文件（0x0.st / Litterbox）：

```bash
export TELEPRESS_IMAGE_HOST_TYPE=0x0
# Litterbox 指定过期时间：1h / 12h / 24h / 72h
export TELEPRESS_IMAGE_HOST_TYPE=litterbox
export TELEPRESS_IMAGE_HOST_EXPIRATION=24h
```

0x0.st 与 Litterbox 均为匿名临时文件托管，文件到期会被删除，不适合作为
长期文章的图片来源。各 Provider 的自定义字符串（userhash、API key、
public/private key、secret 等）都会按 `TELEPRESS_IMAGE_HOST_*` 通用映射
写入 `image_host` 配置。

环境变量的优先级高于配置文件：

```bash
export TELEPRESS_IMAGE_HOST_TYPE=imgbb
export TELEPRESS_IMAGE_HOST_API_KEY=your-key
```

配置文件查找顺序：

1. 传给 `load_config()` 的显式路径
2. `TELEPRESS_CONFIG`
3. `~/.telepress.json`、`~/.telepress.yaml`、`~/.telepress.yml`
4. `~/.config/telepress.json`

## Python API

```python
from telepress import TelegraphPublisher, publish, publish_text

url = publish("article.md", title="我的文章")
text_url = publish_text("# 标题\n\n正文", title="示例")

publisher = TelegraphPublisher(image_size_limit=10)
gallery_url = publisher.publish("gallery.zip", title="图集")
```

直接上传图片：

```python
from telepress import ImageUploader

uploader = ImageUploader("imgbb", api_key="your-key")
url = uploader.upload("photo.jpg")

batch = uploader.upload_batch(["1.jpg", "2.jpg"])
print(batch.success_rate, batch.get_url_map())
```

## 行为与限制

- Markdown 和纯文本会转换为 Telegraph DOM 节点。
- 可以识别 `Chapter 1`、`第一章` 等纯文本章节标题。
- 大文本会在约 10,000 字符边界自动分页，并生成上一页、下一页导航。
- 图集每 100 张图片分页。
- 单张图片默认限制为 5 MiB，超限时自动压缩；GIF 不会自动压缩。
- 处理前会应用 2 GiB 的输入安全上限。
- 默认使用 `~/.telepress_cache.json` 避免重复发布相同文本。

支持 `.txt`、`.md`、`.markdown`、`.rst`、`.text`、`.jpg`、`.jpeg`、
`.png`、`.gif`、`.webp`、`.bmp` 和 `.zip`。

## 错误处理

```python
from telepress import TelePressError, ValidationError, publish

try:
    url = publish("article.md")
except ValidationError as exc:
    print(f"输入无效：{exc}")
except TelePressError as exc:
    print(f"发布失败：{exc}")
```

## 开发与发版

```bash
python -m pip install --editable ".[dev]"
python -m pytest --cov
python -m build
python -m twine check dist/*
```

贡献规范见 [CONTRIBUTING.md](CONTRIBUTING.md)，自动发版的配置和操作步骤见
[docs/en/RELEASING.md](docs/en/RELEASING.md)，版本变化记录在 [CHANGELOG.md](CHANGELOG.md)。

## License

[MIT](LICENSE)
