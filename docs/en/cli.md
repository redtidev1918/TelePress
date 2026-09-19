# CLI

**Language / 语言:** English · [中文](../cli.md)

## Commands

```text
telepress <file> [options]        # same as publish
telepress publish <file> [options]
telepress configure
telepress check
telepress install-rclone
```

## publish

```
telepress publish article.md --title "My article" \
  --image-size-limit 10 --no-compress --api-url http://localhost:9009
```

| Option | Description |
| --- | --- |
| `file` | File to publish |
| `--title` | Page title; defaults to filename |
| `--token` | Explicit Telegraph token (optional) |
| `--image-size-limit` | Max image size in MiB (default 5) |
| `--no-compress` | Do not auto-compress oversized images |
| `--api-url` | Custom Telegraph-compatible API URL |

## configure / check

```bash
telepress configure   # interactive image-host setup
telepress check       # validate image-host config
```
