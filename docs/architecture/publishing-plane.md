# 发布平面

**Language / 语言:** [中文](publishing-plane.md) · [English](../en/architecture/publishing-plane.md)

## 是什么

TelePress 是一个 **Preview / Publishing Plane**：

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

输入可以是任何来源的内容；输出始终是公开可以预览的 Telegraph URL。

## 它不是什么

- 不是内容发现器
- 不是审核系统
- 不是调度器
- 不是 Telegram Bot
- 不持有上游平台业务状态
- 不持有 Pixiv / DeviantArt 等源站账号凭据

## 长期不变量

- stateless-ish：不做业务数据库
- provider neutral：图床、上游来源都不能固化成架构
- source-platform neutral：不写死具体平台的特殊核心模型
- 结构化失败：调用方能按 stage / status 归因
- 已有发布路径向后兼容：不能因为新增富媒体能力而摧毁纯文本 / multipart 图集路径

## AGENTS 约束

仓库长期约束与禁止项见 [AGENTS.md](../../AGENTS.md)。
