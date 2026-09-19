# Security Boundary

**Language / 语言:** English · [中文](../../operations/security.md)

## API key

- With `TELEPRESS_API_KEY` set, `/publish/*` requires a Bearer key or
  `X-TelePress-Key`.
- Without it, the endpoint is open: loopback / internal use only.

## Remote fetch / proxy

- Gallery remote media is opt-in (`TELEPRESS_ALLOW_REMOTE_GALLERY_MEDIA=1`).
- Only `https://`, 50 MiB per file.
- The media proxy rewrites only allowlisted hosts; it is not an open proxy.
- No upstream credentials are forwarded.

## SSRF mitigation

- The media-proxy host allowlist is the only rewritable source set.
- Gallery remote fetch allows https only with a 50 MiB cap.
- Unlisted rich-novel manifest entries always fall back to image-host upload.

## Plain HTTP

Do not bind `telepress-server` directly to a public IP unless behind an
internal network, VPN, or a TLS reverse proxy.
