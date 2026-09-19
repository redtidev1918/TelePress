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

## 导出

`telepress` 包从 `__init__.py` 导出：

- `TelegraphPublisher`、`ImageUploader`、`UploadResult`、`BatchUploadResult`
- 图床类：`ImgbbHost`、`ImgurHost`、`SmmsHost`、`CatboxHost`、`FreeImageHost`、
  `UploadcareHost`、`ImageKitHost`、`CloudinaryHost`、`ZeroXZeroHost`、
  `LitterboxHost`、`R2Host`、`S3Host`、`CustomHost`
- `create_image_host`、`load_config`、`get_image_host_config`
- 异常：`TelePressError`、`ValidationError`、`UploadError`、`AuthenticationError`、
  `SecurityError`、`DependencyError`、`ConversionError`
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
