# 图床

**Language / 语言:** [中文](image-hosts.md) · [English](../en/media/image-hosts.md)

## 支持列表

| Provider | 类型 | 需要凭据 | 永久 | 图片/任意文件 | 已知限制 |
| --- | --- | --- | --- | --- | --- |
| ImgBB | 图片 | API key | 是 | 图片 | 只适合图片 |
| Imgur | 图片 | Client ID | 是 | 图片 | 只适合图片 |
| sm.ms | 图片 | API token | 是 | 图片 | 重复图片会返回已有 URL |
| Freeimage.host | 图片 | API key | 是 | 图片 | — |
| ImageKit | 图片/CDN | private key | 是 | 任意文件 | — |
| Cloudinary | 图片/CDN | cloud name + unsigned preset | 是 | 图片 | unsigned preset 模式 |
| Catbox | 任意文件 | 匿名免凭据，或 userhash | 是 | 任意文件 | 不自动压缩 |
| Uploadcare | 任意文件/CDN | public key | 是 | 任意文件 | 需要 store 策略 |
| 0x0.st | 临时文件 | 无 | 否 | 任意文件 | 到期删除 |
| Litterbox | 临时文件 | 无 | 否 | 任意文件 | 到期删除 |
| S3 / R2 / OSS / MinIO | S3 兼容 | access key | 是 | 任意文件 | 需要 public_url / endpoint |
| Rclone remote | 任意 | remote 配置 | 视远端 | 任意文件 | 需要本机 rclone |
| 自定义 HTTP | 任意 | upload_url | 视服务 | 任意文件 | 需要按响应映射返回 URL |

## 配置

所有 Provider 的环境变量都按 `TELEPRESS_IMAGE_HOST_*` 映射到 `image_host`：

```bash
export TELEPRESS_IMAGE_HOST_TYPE=catbox
export TELEPRESS_IMAGE_HOST_USERHASH=YOUR_USERHASH
```

也可以用 `telepress configure` 交互配置，或写 `~/.telepress.json`。完整配置见
[configuration.md](../configuration.md)。
