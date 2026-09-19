# AGENTS.md —— telepress 是「发布平面」

写给任何进入本仓库的智能体或工程师。跨仓库的职责与执行纪律的唯一权威在：

* `pixivflow-telepost-deploy/AGENTS.md`（PixivFlow Ecosystem Agent Operating Contract）
* `pixivflow-telepost-deploy/docs/architecture/ecosystem-platform.md`（长期架构）
* `pixivflow-telepost-deploy/docs/operations/current-state.md`（当前生产状态）
* `pixivflow-telepost-deploy/CONTRACT.md`（生效生产合同）

本文件只保留本仓边界与特殊约束。本仓职责：telepress 负责把已经过审的内容
发布为富媒体（Markdown / 图片 / Telegraph preview / Catbox），并通过 `/publish/rich-novel` 返回
`{url, assets[]}` 供 PixivFlow 注入 novel_preview_url。

## 一句话

Publishing Plane。它**不持有** Pixiv 凭据、Telegram bot token、channel id 或
TelePost submit token；它只从请求拿到已审核内容与图片，把它们安全地上传到 Catbox /
Telegraph，然后返回可公开预览 URL。

## 硬约束

- **无状态**：不上传不写库（除必要缓存外）；每次 `/publish/rich-novel` 是独立请求，
  幂等可重试，不得依赖同一个服务进程的内存状态。
- **凭据隔离**：只使用自己的 `TELEGRAPH_ACCESS_TOKEN` / `TELEPRESS_API_KEY`
  （运行时 secret，绝不提交仓库）。禁止把上游传过来的任何凭据转发到第三方。
- **内容边界**：只发布 PixivFlow/TelePost 送来的已审核内容；不做审核判断、不做
  moderation、不改业务状态。
- **异常要解释**：失败必须返回结构化错误（stage / code / reason），不得只回通用 500；
  让上游能按 `telepress_publish` stage 归因。
- **Pixiv 媒体代理优先、图床 fallback**：`/publish/rich-novel` 可接收
  `manifest`（`[{"local", "source"}]`）；当配置 `TELEPRESS_PIXIV_PROXY_BASE` 且
  `source` 是 `https://i.pximg.net/...` 时改写为 `<base>/pixiv/...` 并返回
  `status=proxied`。没有 proxy / 不匹配时继续走现有 ImageHost 上传，绝不把任意
  URL 当作可代理上游（固定 `i.pximg.net`，Worker 只允许 GET/HEAD）。
- **保持旧 TXT 兼容**：富媒体是增量能力；不能摧毁已存在的纯文本发布路径。

## 改完请自证

- 本地测试（pytest 或仓库既有 runner）全绿；样例请求（含真实或 mock 图片）能跑通
  `/publish/rich-novel`。
- 缺失/占位 secret 时必须显式 SKIP 或 FAIL，禁止静默绕过鉴权。
