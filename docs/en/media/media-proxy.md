# Generic CDN Media Proxy

**Language / 语言:** English · [中文](../../media/media-proxy.md)

The generic CDN proxy rewrites only https CDN URLs whose host is in an explicit
allowlist to a fixed proxy entry. It is not an open proxy.

## Configuration

| Variable | Description |
| --- | --- |
| `TELEPRESS_MEDIA_PROXY_BASE` | Proxy base URL, e.g. `https://media.example.com` |
| `TELEPRESS_MEDIA_PROXY_HOSTS` | Comma-separated upstream host allowlist |
| `TELEPRESS_MEDIA_PROXY_PATH_PREFIX` | Optional route prefix, default `media` |

Rewrite result:

```text
<base>/<prefix>/<host>/<path>
```

Example:

```bash
export TELEPRESS_MEDIA_PROXY_BASE=https://media.example.com
export TELEPRESS_MEDIA_PROXY_HOSTS=cdn-a.example.com
# https://cdn-a.example.com/full/001.jpg → https://media.example.com/media/cdn-a.example.com/full/001.jpg
```

## Security invariants

- https only
- explicit host allowlist
- not an open proxy
- no arbitrary upstream credentials
- unlisted entries fall back to image-host upload

## Legacy alias

`TELEPRESS_PIXIV_PROXY_BASE` remains only as a backwards-compatible alias:

- allowlist `i.pximg.net`
- rewrite to `<base>/pixiv/<path>`

Use `TELEPRESS_MEDIA_PROXY_*` for new configurations.
