# 图片与媒体

**Language / 语言:** [中文](README.md) · [English](../en/media/README.md)

## 两条媒体解决策略

TelePress 把「上传」和「代理」视为两种不同策略，而不是都塞进「图片托管」。在上传路径中，超过单图限制的可压缩格式会先由 libvips/pyvips 按需读取、缩放并尝试有界 JPEG/WebP 压缩；小文件原样保留，GIF 不自动重编码。

默认单图限制为 5 MiB；可通过 CLI 的 `--image-size-limit` 调整，或用 `--no-compress` 关闭自动压缩。压缩失败会以结构化转换错误返回，不会静默发布未满足限制的文件。

```text
MediaReference
      │
      ├── Proxy path
      │     TELEPRESS_MEDIA_PROXY_*
      │
      └── Upload path
            ImageUploader / ImageHost
```

| 文档 | 内容 |
| --- | --- |
| [media-reference.md](media-reference.md) | MediaReference 数据模型 |
| [media-proxy.md](media-proxy.md) | 通用 CDN 代理、安全不变量、Legacy 兼容 |
| [image-hosts.md](image-hosts.md) | 图床 Provider 清单 |
