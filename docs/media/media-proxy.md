# 通用 CDN 媒体代理

**Language / 语言:** [中文](media-proxy.md) · [English](../en/media/media-proxy.md)

通用 CDN 代理只负责把「明确 allowlist 中的 https CDN URL」改写为固定的代理入口；
它不是一个开放代理，也不是某个平台专属功能。

## 配置

| 环境变量 | 说明 |
| --- | --- |
| `TELEPRESS_MEDIA_PROXY_BASE` | 代理入口 base URL，例如 `https://media.example.com` |
| `TELEPRESS_MEDIA_PROXY_HOSTS` | 允许改写的上游 CDN host 逗号列表，例如 `cdn-a.example.com,cdn-b.example.com` |
| `TELEPRESS_MEDIA_PROXY_PATH_PREFIX` | 可选路由前缀，默认 `media` |

改写结果：

```text
<base>/<prefix>/<host>/<path>
```

示例：

```bash
export TELEPRESS_MEDIA_PROXY_BASE=https://media.example.com
export TELEPRESS_MEDIA_PROXY_HOSTS=cdn-a.example.com
# https://cdn-a.example.com/full/001.jpg
# → https://media.example.com/media/cdn-a.example.com/full/001.jpg
```

## 安全不变量

- 只接受 `https` 源
- 只改写 host 在显式 allowlist 中的条目
- 未命中时退回图床上传，绝不当作可代理上游
- 不转发任意上游凭据
- 因此不会成为开放代理 / SSRF 面

## Legacy 兼容

`TELEPRESS_PIXIV_PROXY_BASE` 仅作为向后兼容别名保留：

- 只放行 `i.pximg.net`
- 改写为 `<base>/pixiv/<path>`

新配置请使用通用的 `TELEPRESS_MEDIA_PROXY_*`。
