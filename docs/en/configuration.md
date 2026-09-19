# Configuration

**Language / 语言:** English · [中文](../configuration.md)

## Config precedence

1. Explicit path passed to `load_config()`
2. `TELEPRESS_CONFIG` environment variable
3. `~/.telepress.json`, `~/.telepress.yaml`, `~/.telepress.yml`
4. `~/.config/telepress.json`
5. Environment variables override

## Telegraph token

Stored by default at `~/.telegraph_token`. Explicit tokens can be passed via
`--token` (CLI) or `token` (REST).

## Image-host config

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

Environment variables map `TELEPRESS_IMAGE_HOST_*` to `image_host`:

```bash
export TELEPRESS_IMAGE_HOST_TYPE=imgbb
export TELEPRESS_IMAGE_HOST_API_KEY=your-key
```

See [media/image-hosts.md](media/image-hosts.md) for the provider list.

## REST / media related

| Variable | Purpose |
| --- | --- |
| `TELEPRESS_API_KEY` | Bearer key for `/publish/*`; unset keeps endpoint open |
| `TELEPRESS_ALLOW_REMOTE_GALLERY_MEDIA=1` | Enable optional remote gallery media |
| `TELEPRESS_MEDIA_PROXY_BASE` | Generic media proxy base URL |
| `TELEPRESS_MEDIA_PROXY_HOSTS` | Comma-separated upstream CDN host allowlist |
| `TELEPRESS_MEDIA_PROXY_PATH_PREFIX` | Proxy route prefix, default `media` |
| `TELEPRESS_PIXIV_PROXY_BASE` | Legacy compatibility alias |
