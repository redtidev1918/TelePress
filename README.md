# TelePress

[![CI](https://github.com/redtidev1918/TelePress/actions/workflows/ci.yml/badge.svg)](https://github.com/redtidev1918/TelePress/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/telepress.svg)](https://pypi.org/project/telepress/)
[![Python](https://img.shields.io/pypi/pyversions/telepress.svg)](https://pypi.org/project/telepress/)
[![Docs](https://img.shields.io/badge/Docs-文档站点-6366f1?style=flat-square)](https://redtidev1918.github.io/TelePress/)

**语言 / Language:** 中文 · [English](README.en.md)

📖 完整文档：<https://redtidev1918.github.io/TelePress/>

TelePress 是一个发布平面：把 Markdown、纯文本、图片和富媒体内容发布为
Telegraph 页面，不关心内容来自哪个平台。

- 纯文本 / Markdown：自动分页并生成上一页、下一页导航
- 图片 / ZIP 图集：压缩后发布为 Telegra.ph 相册
- 富媒体（REST）：通过 `/publish/rich-novel` 发布 Markdown + 本地图
- 图片可在「上传图床」与「通用 CDN 代理」两条路径间选择

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

## 30 秒快速开始

```bash
pip install telepress
telepress article.md --title "我的文章"

# 或者显式子命令
telepress publish article.md --title "我的文章"
```

发布图片 / ZIP 图集前先配置一个图床：

```bash
telepress configure
telepress check
telepress photo.jpg --title "照片"
telepress gallery.zip --title "图集"
```

需要服务化时：

```bash
pip install "telepress[api]"
telepress-server --host 127.0.0.1 --port 8000
# OpenAPI 交互文档：http://127.0.0.1:8000/docs
```

运行时首次使用会自动创建并保存 Telegraph token（默认 `~/.telegraph_token`）。

## 文档

README 不是全量文档；稳定契约放在 `docs/`：

- 快速开始与配置：[getting-started.md](/docs/getting-started.md) · [configuration.md](/docs/configuration.md)
- REST API：[docs/api/README.md](/docs/api/README.md)
- 图片与媒体：[docs/media/README.md](/docs/media/README.md)
- Python API / CLI：[python-api.md](/docs/python-api.md) · [cli.md](/docs/cli.md)
- 架构：[architecture/publishing-plane.md](/docs/architecture/publishing-plane.md)
- 运维与当前状态：[operations/current-state.md](/docs/operations/current-state.md)

## License

[MIT](LICENSE)
