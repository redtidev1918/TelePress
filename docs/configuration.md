# 配置

**Language / 语言:** [中文](configuration.md) · [English](en/configuration.md)

## 配置优先级

1. 传给 `load_config()` 的显式路径
2. `TELEPRESS_CONFIG` 环境变量
3. `~/.telepress.json`、`~/.telepress.yaml`、`~/.telepress.yml`
4. `~/.config/telepress.json`
5. 环境变量（`TELEPRESS_IMAGE_HOST_*` 等）最后覆盖

环境变量优先级高于配置文件。

## Telegraph token

token 默认保存在 `~/.telegraph_token`，由 CLI/API 在需要时自动创建。也可以每次
通过 `--token`（CLI）或 `token`（REST）显式传入。

## 图片托管配置

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

S3 兼容：

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

环境变量按 `TELEPRESS_IMAGE_HOST_*` 映射到 `image_host`：

```bash
export TELEPRESS_IMAGE_HOST_TYPE=imgbb
export TELEPRESS_IMAGE_HOST_API_KEY=your-key
```

完整 Provider 清单与凭据要求见 [media/image-hosts.md](media/image-hosts.md)。

## REST API 相关配置

| 环境变量 | 作用 |
| --- | --- |
| `TELEPRESS_API_KEY` | `/publish/*` 的 Bearer key；未设置则保持开放（仅建议回环/内网） |
| `TELEPRESS_ALLOW_REMOTE_GALLERY_MEDIA=1` | 开启 `/publish/gallery` 的可选远程 media manifest 抓取 |
| `TELEPRESS_MEDIA_PROXY_BASE` | 通用媒体代理入口 base URL |
| `TELEPRESS_MEDIA_PROXY_HOSTS` | 允许改写的上游 CDN host 逗号列表 |
| `TELEPRESS_MEDIA_PROXY_PATH_PREFIX` | 媒体代理路由前缀，默认 `media` |
| `TELEPRESS_PIXIV_PROXY_BASE` | 旧版兼容别名（详见 [media/media-proxy.md](media/media-proxy.md)） |
