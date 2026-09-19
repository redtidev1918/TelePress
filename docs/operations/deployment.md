# 部署

**Language / 语言:** [中文](deployment.md) · [English](../en/operations/deployment.md)

## CLI / 脚本用法

CLI 不需要服务进程：

```bash
pip install telepress
telepress article.md --title "示例"
```

## REST API 服务

```bash
pip install "telepress[api]"
export TELEPRESS_API_KEY=your-key
telepress-server --host 127.0.0.1 --port 8000
```

推荐绑 `127.0.0.1` 或仅内网/Docker 网络；不要把未设 key、明文 HTTP 的发布接口暴露公网。

## 无域名 / 公网 IP

TelePress 与 Bot 同机时保持回环部署即可。若确实需要给受信外部客户端开放公网 IP，
见安全边界 [security.md](security.md) 与跨仓库手册
（`deviantdrop/docs/VPS-public-ip.md`）。
