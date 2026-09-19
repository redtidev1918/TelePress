# 安全边界

**Language / 语言:** [中文](security.md) · [English](../en/operations/security.md)

## API key

- `TELEPRESS_API_KEY` 设置后，`/publish/*` 需要 `Authorization: Bearer <key>` 或 `X-TelePress-Key: <key>`。
- 未设置 key 时是开放模式，**只能用于回环/内网**，严禁直接暴露公网。

## 远程抓取（gallery media / proxy）

- 远程 gallery media 是 opt-in：`TELEPRESS_ALLOW_REMOTE_GALLERY_MEDIA=1`。
- 只接受 `https://`，单文件 50 MiB 上限。
- 媒体代理只改写显式 allowlist 的 host，不会成为开放代理。
- 不转发上游凭据。

## SSRF 缓解

- media proxy 的 host allowlist 是唯一可改写的来源集合。
- gallery 远程抓取只有 https + 50 MiB 上限，不放行任意本机 URL 到内网。
- rich-novel manifest 只有在命中 allowlist 时才改写，其他全部走图床上传。

## 明文 HTTP

除非通过内网 / VPN / 反向代理套 TLS，否则不要把 `telepress-server` 直接绑公网 IP。
