# Media

**Language / 语言:** English · [中文](../../media/README.md)

TelePress treats uploading and proxying as two distinct resolution strategies. On the upload path, oversized compressible images are processed with demand-driven libvips/pyvips loading, resizing, and bounded JPEG/WebP encoding; small files are preserved as-is and GIFs are not re-encoded automatically.

The default per-image limit is 5 MiB. Adjust it with the CLI `--image-size-limit` option, or disable automatic compression with `--no-compress`. Compression failures are surfaced as structured conversion errors rather than silently publishing an image that still exceeds the limit.

```text
MediaReference
      │
      ├── Proxy path
      │     TELEPRESS_MEDIA_PROXY_*
      │
      └── Upload path
            ImageUploader / ImageHost
```

| Document | Content |
| --- | --- |
| [media-reference.md](media-reference.md) | MediaReference model |
| [media-proxy.md](media-proxy.md) | Generic CDN proxy and security invariants |
| [image-hosts.md](image-hosts.md) | Image-host providers |
