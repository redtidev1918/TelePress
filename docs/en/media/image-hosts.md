# Image Hosts

**Language / 语言:** English · [中文](../../media/image-hosts.md)

## Providers

| Provider | Kind | Credentials | Permanent | Images / any file | Known limits |
| --- | --- | --- | --- | --- | --- |
| ImgBB | image | API key | yes | images | images only |
| Imgur | image | Client ID | yes | images | images only |
| sm.ms | image | API token | yes | images | dedupe returns existing URL |
| Freeimage.host | image | API key | yes | images | — |
| ImageKit | image/CDN | private key | yes | any file | — |
| Cloudinary | image/CDN | cloud name + unsigned preset | yes | images | unsigned preset |
| Catbox | any file | anonymous or userhash | yes | any file | no re-compression |
| Uploadcare | any file/CDN | public key | yes | any file | storage policy |
| 0x0.st | temporary | none | no | any file | expiry |
| Litterbox | temporary | none | no | any file | expiry |
| S3 / R2 / OSS / MinIO | S3-compatible | access key | yes | any file | public_url / endpoint |
| Rclone remote | any | remote config | depends | any file | local rclone |
| custom HTTP | any | upload_url | depends | any file | response URL mapping |

## Configuration

All providers read `TELEPRESS_IMAGE_HOST_*` and map into `image_host`:

```bash
export TELEPRESS_IMAGE_HOST_TYPE=catbox
export TELEPRESS_IMAGE_HOST_USERHASH=YOUR_USERHASH
```

Use `telepress configure` interactively or write `~/.telepress.json`. See
[configuration.md](../configuration.md).
