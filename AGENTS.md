# AGENTS.md — telepress 是「发布平面」

给进入本仓库的智能体/工程师的长期不变量。本文件不描述某一具体图床、某个上游平台
或某个临时 Worker URL，只记录 TelePress 作为通用发布平面的稳定边界。

## 一句话

TelePress = **Preview / Publishing Plane**。它把请求里的内容与媒体引用转换成可公开
预览的 Telegraph URL，并返回结构化结果给调用方。

## 必须保持

- **无状态（stateless-ish）**：除必要缓存外不写库；单次发布是独立、可重试请求，不得依赖服务进程内存状态。
- **平台中立（provider neutral）**：不持有 Pixiv / DeviantArt 等源站平台账号凭据。
- **源平台中立（source-platform neutral）**：内容来源与 TelePress 发布能力无关。
- **不持有上游业务状态**：不做审核、不做 moderation、不作调度器、不是 Telegram Bot。
- **结构化失败**：错误必须带上 stage / code / reason，便于调用方归因（例如 `/publish/rich-novel` 的 `assets[].status`）。
- **向后兼容**：不能因为新增富媒体能力而摧毁已存在的纯文本 / 文件 / multipart 图集发布路径。

## 媒体

`MediaReference` 是媒体解析的统一入口：

```text
MediaReference
      │
      ├── Proxy path
      │     TELEPRESS_MEDIA_PROXY_*（显式 host allowlist 命中时）
      │
      └── Upload path
            ImageUploader / ImageHost（fallback 或未启用 proxy）
```

规则：

- 命中的 `https` 且 host 在允许列表内 → 走 proxy，状态 `proxied`；
- 其他场景 → 走图床上传，失败状态 `failed`；
- 代理必须是「固定上游、仅 https、只改写 allowlist host」的受限代理，绝不能变成开放代理或任意 URL SSRF。

## 不要

- 给 Pixiv / DeviantArt 等具体来源写特殊核心模型；
- 把某个图床（例如 Catbox）当成架构本身；
- 建立业务数据库；
- 接管上游平台凭据；
- 新建平行 Renderer / Publisher / Media Resolver pipeline（新的发布路径必须复用现有管道）。

## 改完请自证

- 本地测试全绿：`python -m pytest --cov`
- 样例请求能跑通受影响路径（至少含 `/publish/*` 或 CLI 发布）
- 缺失/占位 secret 时必须显式 SKIP 或 FAIL，禁止静默绕过鉴权
