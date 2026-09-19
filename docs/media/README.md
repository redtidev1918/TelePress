# 图片与媒体

**Language / 语言:** [中文](README.md) · [English](../en/media/README.md)

## 两条媒体解决策略

TelePress 把「上传」和「代理」视为两种不同策略，而不是都塞进「图片托管」：

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
