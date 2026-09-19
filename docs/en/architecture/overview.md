# Architecture Overview

**Language / 语言:** English · [中文](../../architecture/overview.md)

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

## Components

- **Renderer**: Markdown / text → Telegraph DOM nodes, with pagination.
- **Media Resolver**: resolves a `MediaReference` to a public URL via the proxy
  or upload path.
- **Telegraph Publisher**: creates pages and pagination through the Telegraph API.

## Properties

- Stateless publishing (only required local caches)
- No upstream platform credentials or business state
- Structured failure: each asset is `uploaded` / `proxied` / `failed`
