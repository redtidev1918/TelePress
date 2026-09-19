# 架构概览

**Language / 语言:** [中文](overview.md) · [English](../en/architecture/overview.md)

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

## 组件

- **Renderer**：Markdown / 纯文本 → Telegraph DOM 节点，并负责分页。
- **Media Resolver**：把 `MediaReference` 解析为可公开访问的 URL：
  - Proxy path（allowlist 命中的 https）
  - Upload path（ImageHost fallback）
- **Telegraph Publisher**：调用 Telegraph API 创建页面，生成分页与导航。

## 关键性质

- 无状态发布（只做必要本地缓存）
- 不持有上游平台凭据或业务状态
- 结构化失败：每个 media asset 能区分为 uploaded / proxied / failed
