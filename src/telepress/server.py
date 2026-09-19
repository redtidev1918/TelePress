try:
    from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Header, Security
    from pydantic import BaseModel
    from starlette.concurrency import run_in_threadpool
except ImportError as exc:  # pragma: no cover - exercised only without [api]
    raise ImportError(
        'The TelePress API server needs optional dependencies. '
        'Install them with: pip install "telepress[api]"'
    ) from exc
from typing import Optional, List, Dict
import os
import hmac
import shutil
import tempfile
import zipfile
import urllib.request
from .core import TelegraphPublisher
from .exceptions import TelePressError, ValidationError

app = FastAPI(
    title="TelePress API",
    description="REST API to convert text, markdown, images, and zips to Telegraph pages.",
    version="0.1.0"
)

# —— 请求级鉴权（可选）：设置环境变量 TELEPRESS_API_KEY 后，/publish/* 需要携带
#    `Authorization: Bearer <key>` 或 `X-TelePress-Key: <key>`。未设置时保持开放（向后兼容），
#    但请勿把无鉴权的发布接口暴露公网——建议绑 127.0.0.1 / 内网或 Docker 网络。
def require_api_key(
    authorization: Optional[str] = Header(None),
    x_telepress_key: Optional[str] = Header(None, alias="X-TelePress-Key"),
):
    expected = os.environ.get("TELEPRESS_API_KEY", "").strip()
    if not expected:
        return True  # 未配置 key：放行（开发/本地场景）
    presented = None
    if authorization and authorization.lower().startswith("bearer "):
        presented = authorization[7:].strip()
    elif x_telepress_key:
        presented = x_telepress_key.strip()
    if not presented or not hmac.compare_digest(presented, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True

# 所有发布端点共用的鉴权依赖。
_api_auth = [Security(require_api_key)]


# Request Models
class TextPublishRequest(BaseModel):
    content: str
    title: str
    token: Optional[str] = None

class PublishResponse(BaseModel):
    url: str
    status: str = "success"

class GalleryPublishResponse(BaseModel):
    url: str
    status: str = "success"
    ok: bool = True
    files: int = 0

class RichNovelAsset(BaseModel):
    local: str
    remote: Optional[str] = None
    status: str = "uploaded"
    assetId: Optional[str] = None

class RichNovelResponse(BaseModel):
    url: str
    status: str = "success"
    assets: List[RichNovelAsset] = []

def get_publisher(token: Optional[str] = None):
    try:
        return TelegraphPublisher(token=token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _write_text_temp(content: str) -> str:
    """Write request text without blocking the async event loop."""
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.md', delete=False, encoding='utf-8'
    ) as tmp:
        tmp.write(content)
        return tmp.name


def _copy_upload_temp(file_obj, suffix: str) -> str:
    """Copy an uploaded file into a stable temporary path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file_obj, tmp)
        return tmp.name


def _build_gallery_footer(
    tags: Optional[str],
    link: Optional[str],
    spoiler: Optional[str]
) -> List[Dict]:
    """
    Build the first-page footer nodes for a gallery from optional metadata.
    
    Renders an adult/nsfw warning when spoiler is truthy, a #tag paragraph, and a
    source link paragraph. Returns [] when nothing is provided.
    """
    nodes: List[Dict] = []
    if spoiler and str(spoiler).strip().lower() in ('1', 'true', 'yes', 'on'):
        nodes.append({
            'tag': 'p',
            'children': ['⚠️ Contains adult content / 成人内容']
        })
    if tags:
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        if tag_list:
            nodes.append({
                'tag': 'p',
                'children': ['# ' + ' #'.join(tag_list)]
            })
    if link and str(link).strip():
        link = link.strip()
        nodes.append({
            'tag': 'p',
            'children': [
                'Source: ',
                {'tag': 'a', 'attrs': {'href': link}, 'children': [link]}
            ]
        })
    return nodes



def _gallery_remote_media_enabled() -> bool:
    """Remote MediaReference fetch for /publish/gallery is opt-in.

    Off by default so a loopback-only TelePress (no place behind a public
    reverse proxy) never becomes an open fetch proxy. Set
    ``TELEPRESS_ALLOW_REMOTE_GALLERY_MEDIA=1`` only if you accept the blast
    radius of server-side URL fetching (https-only, 50 MiB cap) for your own
    clients.
    """
    return os.environ.get("TELEPRESS_ALLOW_REMOTE_GALLERY_MEDIA", "").strip().lower() in ("1", "true", "yes", "on")


def _publish_gallery_worker(
    files,
    title: Optional[str],
    tags: Optional[str],
    link: Optional[str],
    spoiler: Optional[str],
    token: Optional[str],
    media_fetched: Optional[list] = None
) -> Dict:
    """
    Save the uploaded images in order, pack them into a zip, and publish them
    as a Telegra.ph gallery. Runs off the async event loop because publishing
    performs synchronous HTTP requests and may wait for rate limits.
    """
    tmp_dir = tempfile.mkdtemp(prefix='telepress-gallery-')
    try:
        files = files or []
        media_fetched = media_fetched or []
        paths = []
        used_names = set()
        for index, upload in enumerate(files, start=1):
            raw_name = os.path.basename(upload.filename or '')
            filename = raw_name or f'image_{index}.jpg'
            base, ext = os.path.splitext(filename)
            candidate = filename
            counter = 1
            while candidate in used_names:
                candidate = f'{base}_{counter}{ext}'
                counter += 1
            used_names.add(candidate)
            dest = os.path.join(tmp_dir, candidate)
            with open(dest, 'wb') as out:
                shutil.copyfileobj(upload.file, out)
            paths.append(dest)

        for index, ref in enumerate(media_fetched, start=1):
            if not isinstance(ref, dict):
                raise ValidationError(f"media[{index}] entries must be objects")
            source = ref.get('sourceUrl') or ref.get('source') or ref.get('source_url')
            if not source or not str(source).startswith('https://'):
                raise ValidationError(f"media[{index}] sourceUrl must be an https URL")
            filename = str(ref.get('filename') or f'image_{index + len(files)}.jpg')
            candidate = os.path.basename(filename) or f'image_{index + len(files)}.jpg'
            counter = 1
            while candidate in used_names:
                base, ext = os.path.splitext(candidate)
                candidate = f'{base}_{counter}{ext}'
                counter += 1
            used_names.add(candidate)
            dest = os.path.join(tmp_dir, candidate)
            total = 0
            try:
                with urllib.request.urlopen(source, timeout=60) as resp, open(dest, 'wb') as out:
                    while True:
                        chunk = resp.read(1024 * 1024)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > 50 * 1024 * 1024:
                            raise ValidationError(f"media[{index}] exceeds the 50 MiB gallery cap")
                        out.write(chunk)
            except ValidationError:
                raise
            except Exception as exc:
                raise ValidationError(f"media[{index}] could not be fetched: {exc}") from exc
            paths.append(dest)

        if not paths:
            raise ValidationError("No files or media provided for gallery publishing")

        zip_path = os.path.join(tmp_dir, 'gallery.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for p in paths:
                zf.write(p, arcname=os.path.basename(p))

        footer = _build_gallery_footer(tags, link, spoiler)
        pub_title = title or os.path.splitext(os.path.basename(paths[0]))[0]
        publisher = get_publisher(token)
        url = publisher.publish_zip_gallery(
            zip_path, title=pub_title, footer_nodes=footer
        )
        return {'url': url, 'files': len(paths)}
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _publish_rich_novel_worker(
    md_file,
    image_files,
    title: Optional[str],
    token: Optional[str],
    manifest: Optional[list] = None,
) -> Dict:
    """
    Save an uploaded markdown + image set, upload the images, render Telegraph
    nodes and return ``{url, assets}``. Runs off the async event loop because
    publishing performs synchronous HTTP requests.

    ``manifest`` is optional: ``[{"local": "<md rel path>", "source": "<CDN
    URL>"}]``. Sources whose host is in the configured media-proxy allowlist
    are rewritten to proxy URLs instead of being uploaded to an image host.
    """
    tmp_dir = tempfile.mkdtemp(prefix='telepress-rich-')
    try:
        md_suffix = os.path.splitext(md_file.filename or 'novel.md')[1] or '.md'
        md_path = os.path.join(tmp_dir, 'novel' + md_suffix)
        with open(md_path, 'wb') as out:
            shutil.copyfileobj(md_file.file, out)

        for upload in image_files:
            filename = (upload.filename or '').replace('\\', '/')
            parts = [p for p in filename.split('/') if p and p not in ('.', '..')]
            if not parts:
                continue
            dest = os.path.join(tmp_dir, *parts)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, 'wb') as out:
                shutil.copyfileobj(upload.file, out)

        publisher = get_publisher(token)
        return publisher.publish_rich_markdown(
            md_path, title=title or 'Novel', manifest=manifest
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "telepress"}

@app.post("/publish/text", response_model=PublishResponse, dependencies=_api_auth)
async def publish_text(request: TextPublishRequest):
    """
    Publish raw Markdown/Text content directly.
    """
    try:
        tmp_path = await run_in_threadpool(_write_text_temp, request.content)
        
        # Publishing performs synchronous HTTP requests and may wait for rate
        # limits, so keep it off the async event loop.
        publisher = await run_in_threadpool(get_publisher, request.token)
        url = await run_in_threadpool(
            publisher.publish, tmp_path, title=request.title
        )
        return PublishResponse(url=url)
        
    except TelePressError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.post("/publish/file", response_model=PublishResponse, dependencies=_api_auth)
async def publish_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    token: Optional[str] = Form(None)
):
    """
    Upload a file (md, txt, zip, image) to be processed and published.
    """
    try:
        suffix = os.path.splitext(file.filename)[1]
        tmp_path = await run_in_threadpool(
            _copy_upload_temp, file.file, suffix
        )
            
        publisher = await run_in_threadpool(get_publisher, token)
        
        # If no title provided, use filename from upload
        pub_title = title if title else file.filename
        
        url = await run_in_threadpool(
            publisher.publish, tmp_path, title=pub_title
        )
        return PublishResponse(url=url)
        
    except TelePressError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.post("/publish/gallery", response_model=GalleryPublishResponse, dependencies=_api_auth)
async def publish_gallery(
    files: Optional[List[UploadFile]] = File(None),
    title: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    link: Optional[str] = Form(None),
    spoiler: Optional[str] = Form(None),
    token: Optional[str] = Form(None),
    media: Optional[str] = Form(None)
):
    """
    Upload multiple image files and publish them as a Telegra.ph gallery.

    Files are packed into a zip in upload order and published with automatic
    pagination and Prev/Next navigation. The optional `tags` (comma-separated),
    `link` (source URL) and `spoiler` (truthy, used to mark adult/nsfw content) fields are
    rendered as a footer on the first page. `title` defaults to the first
    file's name when omitted.

    Compatible with generic multipart delivery clients that post repeated
    `files` parts to this endpoint.

    Optional remote media (opt-in, disabled by default): set
    ``TELEPRESS_ALLOW_REMOTE_GALLERY_MEDIA=1`` and send a `media` JSON form
    field with ``[{"assetId","kind","sourceUrl","filename"}]`` entries. When
    present, TelePress fetches each https sourceUrl server-side (50 MiB cap)
    instead of requiring uploaded bytes, then publishes the same gallery.
    Clients that rely on this path are expected to be either loopback-only or
    protected by the API key, since enabling it turns the endpoint into a
    limited server-side fetch proxy.
    """
    import json as _json
    parsed_media = None
    if media:
        try:
            parsed_media = _json.loads(media)
            if not isinstance(parsed_media, list):
                raise ValueError("media must be a JSON list")
        except (ValueError, _json.JSONDecodeError) as exc:
            raise HTTPException(status_code=400, detail=f"media 解析失败: {exc}")
    if parsed_media and not _gallery_remote_media_enabled():
        raise HTTPException(
            status_code=400,
            detail="remote gallery media is disabled; set TELEPRESS_ALLOW_REMOTE_GALLERY_MEDIA=1 to enable",
        )
    if not files and not parsed_media:
        raise HTTPException(status_code=422, detail="Provide files or media")
    try:
        result = await run_in_threadpool(
            _publish_gallery_worker, files, title, tags, link, spoiler, token,
            parsed_media or [],
        )
        return GalleryPublishResponse(
            url=result['url'], files=result['files']
        )
    except TelePressError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/publish/rich-novel", response_model=RichNovelResponse, dependencies=_api_auth)
async def publish_rich_novel(
    md: UploadFile = File(...),
    images: Optional[List[UploadFile]] = File(None),
    title: Optional[str] = Form(None),
    token: Optional[str] = Form(None),
    manifest: Optional[str] = Form(None)
):
    """
    Publish a rich novel (markdown + local images) to Telegraph.

    ``md`` is the markdown with ``![](images/xxx.jpg)``-style local references;
    each file in ``images`` must carry the same relative path as its markdown
    refs (e.g. ``images/001.jpg``). Images are uploaded to the configured image
    host (Catbox), refs are rewritten to remote URLs, Telegraph nodes are
    rendered in source order and the page is published. Returns the page URL
    plus an ``assets`` map so the caller can see exactly which upload failed.

    ``manifest`` is optional JSON: ``[{"local": "images/001.jpg",
    "source": "https://<cdn>/..."}]``. When a media proxy is configured
    (``TELEPRESS_MEDIA_PROXY_BASE`` + ``TELEPRESS_MEDIA_PROXY_HOSTS``, or the
    legacy ``TELEPRESS_PIXIV_PROXY_BASE`` alias), entries whose host is in the
    allowlist are rewritten to the proxy and returned as ``status: "proxied"``;
    anything else keeps the existing image-host fallback. This is a generic CDN
    rewriter, not a Pixiv-only feature.
    """
    parsed_manifest = None
    if manifest:
        import json as _json
        try:
            parsed_manifest = _json.loads(manifest)
            if not isinstance(parsed_manifest, list):
                raise ValueError("manifest must be a JSON list")
        except (ValueError, _json.JSONDecodeError) as exc:
            raise HTTPException(status_code=400, detail=f"manifest 解析失败: {exc}")
    try:
        result = await run_in_threadpool(
            _publish_rich_novel_worker, md, images or [], title, token,
            parsed_manifest,
        )
        return RichNovelResponse(url=result['url'], assets=result.get('assets', []))
    except TelePressError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_server(host="0.0.0.0", port=8000):
    """Start the TelePress API server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


def main():
    """
    CLI entry point for telepress-server command.
    
    Usage:
        telepress-server
        telepress-server --host 127.0.0.1 --port 9000
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Start the TelePress REST API server."
    )
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host to bind (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to listen on (default: 8000)"
    )
    
    args = parser.parse_args()
    
    print(f"Starting TelePress API server at http://{args.host}:{args.port}")
    print("API docs available at: http://localhost:{}/docs".format(args.port))
    
    start_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
