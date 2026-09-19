# 快速开始

**Language / 语言:** [中文](getting-started.md) · [English](en/getting-started.md)

## 环境要求

- Python 3.10 或更高版本
- Telegraph token（首次使用自动创建并保存到 `~/.telegraph_token`）
- 只有发布图片或图集时才需要配置图床

## 安装

```bash
pip install telepress

# 可选：REST API 服务
pip install "telepress[api]"

# 可选：S3 / R2 / OSS / MinIO 等 S3 兼容图床
pip install "telepress[s3]"

# 可选：YAML 配置
pip install "telepress[yaml]"
```

开发安装：

```bash
git clone https://github.com/redtidev1918/telepress.git
cd telepress
python -m pip install --editable ".[dev]"
```

## 30 秒跑起来

```bash
telepress article.md --title "我的文章"

# 显式子命令写法与此等价
telepress publish article.md --title "我的文章"
```

发布图片 / ZIP 图集前先配置图床：

```bash
telepress configure
telepress check
telepress photo.jpg --title "照片"
telepress gallery.zip --title "图集"
```

常用参数：

```bash
# 临时覆盖图片大小限制（MiB）
telepress gallery.zip --image-size-limit 10

# 不压缩超限图片
telepress gallery.zip --no-compress

# 兼容 Telegraph 的自定义 API
telepress article.md --api-url http://localhost:9009
```

纯文本发布不会加载或要求图床配置；图片 / 图集才依赖图床。

## 服务化

```bash
pip install "telepress[api]"
telepress-server --host 127.0.0.1 --port 8000
```

OpenAPI 交互文档位于 `http://127.0.0.1:8000/docs`。REST 契约见
[api/README.md](api/README.md)。

## 行为与限制

- Markdown 和纯文本会转换为 Telegraph DOM 节点。
- 识别 `Chapter 1`、`第一章` 等纯文本章节标题。
- 大文本约 10,000 字符边界自动分页，并生成上一页、下一页导航。
- 图集每 100 张图片分页。
- 单张图片默认限制 5 MiB，超限自动压缩；GIF 不自动压缩。
- 处理前应用 2 GiB 输入安全上限。
- 默认使用 `~/.telepress_cache.json` 避免重复发布相同文本。
- 支持 `.txt`、`.md`、`.markdown`、`.rst`、`.text`、`.jpg`、`.jpeg`、
  `.png`、`.gif`、`.webp`、`.bmp`、`.zip`。
