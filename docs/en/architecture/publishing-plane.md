# Publishing Plane

**Language / 语言:** English · [中文](../../architecture/publishing-plane.md)

## What it is

TelePress is a **Preview / Publishing Plane**:

```text
Input
  Content / MediaReference
        ↓
TelePress Publishing Plane
        ├─ Renderer
        ├─ Media Resolver
        │    ├─ Proxy
        │    └─ Upload
        └─ Telegraph Publisher
        ↓
Public Preview URL
```

Input may come from any source; the output is always a public Telegraph URL.

## What it is not

- Not a content discovery service
- Not a moderation / review system
- Not a scheduler
- Not a Telegram bot
- Does not hold upstream platform business state
- Does not hold Pixiv / DeviantArt or other source-account credentials

## Long-term invariants

- stateless-ish: no business database
- provider neutral: image hosts and upstreams are interchangeable
- source-platform neutral: no platform-specific core models
- structured failures: callers can attribute by stage / status
- backward compatible: new rich paths never break plain-text / multipart paths

## Agent constraints

See [AGENTS.md](../../../AGENTS.md) for the repository-wide long-term constraints.
