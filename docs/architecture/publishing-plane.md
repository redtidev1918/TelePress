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

## Telegraph 页面大小

20,000 源字符只是分页目标。发布前还必须按 Telegraph Python 客户端的
紧凑 UTF-8 JSON 序列化检查渲染节点，正文每页最多 60 KiB，预留导航空间。
超限正文在节点边界分页；单个超大段落按文本拆分并保留其格式容器。
分页不能丢弃正文，无法拆分的超大媒体属性应明确报错。
追加导航后再次检查 64 KiB 上限，必要时将全页索引缩为当前页 / 总页数。

采用既有 MarkdownConverter / Telegraph Python 客户端，不新增发布管道。
依据：[Telegraph createPage / editPage 官方契约](https://telegra.ph/api)，
两者的 content 上限均为 64 KB；客户端序列化使用 ensure_ascii=False。

## AGENTS 约束

仓库长期约束与禁止项见 [AGENTS.md](../../AGENTS.md)。
