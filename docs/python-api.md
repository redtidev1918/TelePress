# Python API

**Language / 语言:** [中文](python-api.md) · [English](en/python-api.md)

## 发布

```python
from telepress import TelegraphPublisher, publish, publish_text

url = publish("article.md", title="我的文章")
text_url = publish_text("# 标题\n\n正文", title="示例")

publisher = TelegraphPublisher(image_size_limit=10)
gallery_url = publisher.publish("gallery.zip", title="图集")
```

## 图片上传

```python
from telepress import ImageUploader

uploader = ImageUploader("imgbb", api_key="your-key")
url = uploader.upload("photo.jpg")

batch = uploader.upload_batch(["1.jpg", "2.jpg"])
print(batch.success_rate, batch.get_url_map())
```

`ImageUploader()` 不传参数时会从 `~/.telepress.json` / 环境变量加载配置。

### 结构化媒体结果（ResolvedMedia）

`resolve()` 是 `upload()` 的结构化版本：**`upload()` 仍然返回 `str` URL（保持兼容）**，
新增的 `resolve()` 返回 `ResolvedMedia`，携带 provider 限定元数据：

```python
from telepress.media_result import ResolvedMedia, provider_qualify

m = uploader.resolve("photo.jpg", mime_type="image/jpeg")
# ResolvedMedia(url=..., media_id=..., provider=..., mime_type=...)
print(m.url, m.media_id, m.media_uri)   # media_uri: "catbox://abc123"

# 旧 UploadResult 可通过 as_resolved() 升级，字段保持向后兼容
result = uploader.upload_safe("photo.jpg")
if result.success:
    m = result.as_resolved()
```

- `ResolvedMedia.url` 永远是可直接使用的字符串 —— 不破坏 `url = resolve(...)` 这类旧写法。
- `media_uri`（格式 `provider://media_id`）让媒体 ID 不再脱离 Provider 存在，便于将来从
  Provider A 迁移到 Provider B 时保留身份。
- `provider_qualify(provider, media_id)` 是独立辅助函数。

## 导出

`telepress` 包从 `__init__.py` 导出：

- `TelegraphPublisher`、`ImageUploader`、`UploadResult`、`BatchUploadResult`、`ResolvedMedia`
- 图床类：`ImgbbHost`、`ImgurHost`、`SmmsHost`、`CatboxHost`、`FreeImageHost`、
  `UploadcareHost`、`ImageKitHost`、`CloudinaryHost`、`ZeroXZeroHost`、
  `LitterboxHost`、`R2Host`、`S3Host`、`CustomHost`
- `create_image_host`、`load_config`、`get_image_host_config`、`provider_qualify`
- 异常：`TelePressError`、`ValidationError`、`UploadError`、`AuthenticationError`、
  `SecurityError`、`DependencyError`、`ConversionError`、`RetryableError`、
  `RateLimitError`、`ProviderAuthError`、`ProviderPermanentError`
- 常量与工具：`MAX_IMAGE_SIZE`、`MAX_IMAGES_PER_PAGE`、`compress_image_to_size` 等

## 错误处理

```python
from telepress import TelePressError, ValidationError, publish

try:
    url = publish("article.md")
except ValidationError as exc:
    print(f"输入无效：{exc}")
except TelePressError as exc:
    print(f"发布失败：{exc}")
```

错误分层便于上层判断"该不该重试"：

- `UploadError` —— 上传失败（基类，`except UploadError` 仍能捕获所有上传错误）。
- `RetryableError` —— 临时性错误，**可以重试**（超时、连接重置、5xx）。
- `RateLimitError` —— 限流 / 429，**可以重试**，且应遵守 `retry_after` 间隔。
- `ProviderAuthError` —— 认证失败（API key 无效等），**不要重试**。
- `ProviderPermanentError` —— 永久性失败（权限、非法输入、unsupported media），**不要重试**。

上传重试策略已在 `_upload_with_retry` 中按上述分类生效：永久错误直接失败（fail-fast），
可重试错误才走指数退避。所有新异常类都继承自 `UploadError`，因此既有 `except UploadError`
代码无需任何改动。
