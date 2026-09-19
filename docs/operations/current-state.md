# 当前状态

**Language / 语言:** [中文](current-state.md) · [English](../en/operations/current-state.md)

> 动态事实，随时可能变化；不在架构文档里写版本号和临时故障。

## Current release

`0.14.1`

## Current publication paths

| 路径 | 状态 |
| --- | --- |
| text | VERIFIED |
| file | VERIFIED |
| gallery multipart | VERIFIED |
| gallery remote (`media` manifest) | opt-in |
| rich novel | VERIFIED |

## Media proxy

- generic host allowlist implemented（`TELEPRESS_MEDIA_PROXY_*`）
- Legacy：`TELEPRESS_PIXIV_PROXY_BASE` supported as compatibility alias

## Known external dependencies

- Telegraph
- configured ImageHost（可选）
- configured media proxy（可选）
