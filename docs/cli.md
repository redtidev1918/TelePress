# CLI

**Language / 语言:** [中文](cli.md) · [English](en/cli.md)

## 命令概览

```text
telepress <file> [options]        # 发布文件（等价 telepress publish <file>）
telepress publish <file> [options]
telepress configure               # 交互式配置图床
telepress check                   # 检查图床配置
telepress install-rclone          # 帮助安装 Rclone
```

## publish / 直接发布

```
telepress publish article.md --title "我的文章" --token ... \
  --author-name "Alice" --author-url https://example.com/alice \
  --image-size-limit 10 --no-compress --api-url http://localhost:9009
```

| 参数 | 说明 |
| --- | --- |
| `file` | 要发布的文件（md/txt/zip/图片等） |
| `--title` | 页面标题；缺省用文件名 |
| `--token` | 显式 Telegraph token（可选） |
| `--image-size-limit` | 最大图片大小（MiB），默认 5 |
| `--no-compress` | 关闭自动压缩超限图片 |
| `--api-url` | 兼容 Telegraph 的自定义 API 地址 |
| `--author-name` | Telegraph 页面标题下方显示的作者名称 |
| `--author-url` | 点击作者名称后打开的 URL |

## configure / check

```bash
# 交互式选择图床并保存到 ~/.telepress.json 等位置
telepress configure

# 校验当前图床配置是否可用
telepress check
```
