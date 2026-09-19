# Deployment

**Language / 语言:** English · [中文](../../operations/deployment.md)

## CLI / scripts

No server process is required for CLI use:

```bash
pip install telepress
telepress article.md --title "Example"
```

## REST API

```bash
pip install "telepress[api]"
export TELEPRESS_API_KEY=your-key
telepress-server --host 127.0.0.1 --port 8000
```

Bind `127.0.0.1` or an internal / Docker network. Never expose an unkeyed,
plain-HTTP publish endpoint publicly.

## Public IP without a domain

Keep loopback-only when TelePress runs on the same host as downstream
consumers. If you must serve trusted external clients over a public IP, read
[security.md](security.md) and the cross-repo guide in
`deviantdrop/docs/VPS-public-ip.md`.
