import os
import re
import time
import sys
import tempfile
import zipfile
import json
import hashlib
from typing import Optional, List, Dict
from urllib.parse import urlparse
try:
    from telegraph.api import TelegraphApi
except ImportError:
    TelegraphApi = None

from .auth import TelegraphAuth
from .config import load_config
from .converter import NovelMarkdownRenderer
from .uploader import ImageUploader
from .media_proxy import proxy_url as media_proxy_url, reference_from_entry
from .utils import (
    natural_sort_key, safe_extract_zip, validate_file_size,
    MAX_TEXT_SIZE, MAX_IMAGES_PER_PAGE, MAX_IMAGE_SIZE,
    ALLOWED_TEXT_EXTENSIONS, ALLOWED_ARCHIVE_EXTENSIONS, ALLOWED_IMAGE_EXTENSIONS
)
from .exceptions import UploadError, ValidationError
from .interfaces import IPublisher

# Cache file for deduplication
CACHE_FILE = os.path.expanduser("~/.telepress_cache.json")

# Source-text target only; rendered UTF-8 node JSON is bounded separately.
MARKDOWN_PAGE_CHUNK_SIZE = 20_000
TELEGRAPH_CONTENT_LIMIT = 64 * 1024
TELEGRAPH_BODY_LIMIT = 60 * 1024


def _node_json_size(value) -> int:
    """Match telegraph.utils.json_dumps, including multibyte text and escaping."""
    return len(json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))


def _split_large_node(node, limit: int) -> List:
    if _node_json_size(node) <= limit:
        return [node]
    if isinstance(node, str):
        # Find a fitting prefix without cutting a Unicode code point.
        pieces = []
        while node:
            low, high = 0, len(node)
            while low < high:
                mid = (low + high + 1) // 2
                if _node_json_size(node[:mid]) <= limit:
                    low = mid
                else:
                    high = mid - 1
            if not low:
                raise ValidationError("Telegraph content node cannot fit the page limit")
            pieces.append(node[:low])
            node = node[low:]
        return pieces
    if isinstance(node, dict) and node.get('children'):
        wrapper = {**node, 'children': []}
        # Empty children already contribute two brackets to the wrapper size.
        child_limit = limit - _node_json_size(wrapper) + 2
        if child_limit >= 2:
            return [
                {**node, 'children': children}
                for children in _paginate_nodes(node['children'], child_limit)
            ]
    raise ValidationError("Telegraph content node cannot fit the page limit")


def _paginate_nodes(nodes: List, limit: int = TELEGRAPH_BODY_LIMIT) -> List[List]:
    """Pack rendered nodes; split oversized text containers without losing text."""
    pages, current, size = [], [], 2  # JSON array brackets
    for node in nodes:
        for piece in _split_large_node(node, limit - 2):
            piece_size = _node_json_size(piece)
            if current and size + 1 + piece_size > limit:
                pages.append(current)
                current, size = [], 2
            size += piece_size + (1 if current else 0)
            current.append(piece)
    if current:
        pages.append(current)
    return pages or [[]]

def _load_cache() -> Dict:
    """Load published content cache."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def _save_cache(cache: Dict):
    """Save published content cache."""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except:
        pass

def _content_hash(content: str) -> str:
    """Generate hash for content deduplication."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


def _split_markdown_chunks(content: str, chunk_size: int = MARKDOWN_PAGE_CHUNK_SIZE) -> List[str]:
    """Split markdown source text near ``chunk_size`` without cutting short lines.

    Lines longer than one chunk are force-split so publication can still make
    progress. Short lines are kept together until the next line would exceed the
    page target, which preserves paragraph structure for normal novel prose.
    """
    if len(content) <= chunk_size:
        return [content]

    chunks = []
    current_chunk = []
    current_len = 0

    for line in content.splitlines(keepends=True):
        while len(line) > chunk_size:
            if current_chunk:
                chunks.append("".join(current_chunk))
                current_chunk = []
                current_len = 0
            chunks.append(line[:chunk_size])
            line = line[chunk_size:]

        if current_len + len(line) > chunk_size and current_chunk:
            chunks.append("".join(current_chunk))
            current_chunk = []
            current_len = 0

        current_chunk.append(line)
        current_len += len(line)

    if current_chunk:
        chunks.append("".join(current_chunk))

    return chunks

def _validate_author_metadata(author_name: Optional[str], author_url: Optional[str]) -> None:
    """Validate optional Telegraph author metadata."""
    if author_name is not None and not isinstance(author_name, str):
        raise ValidationError("author_name must be a string")

    if author_url is None:
        return
    if not isinstance(author_url, str):
        raise ValidationError("author_url must be a string")
    if any(char.isspace() for char in author_url):
        raise ValidationError("author_url must be a valid URL")

    parsed = urlparse(author_url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        raise ValidationError("author_url must be a valid URL")


def _author_metadata_kwargs(
    author_name: Optional[str], author_url: Optional[str]
) -> Dict[str, str]:
    """Return only the author fields explicitly supplied by the caller."""
    _validate_author_metadata(author_name, author_url)
    kwargs: Dict[str, str] = {}
    if author_name is not None:
        kwargs['author_name'] = author_name
    if author_url is not None:
        kwargs['author_url'] = author_url
    return kwargs


def _patch_telegraph_api(api_url: str):
    """Monkey patch TelegraphApi to support custom base URL."""
    if not TelegraphApi or not api_url:
        return
        
    # Store original methods if not already stored
    if not hasattr(TelegraphApi, '_original_init'):
        TelegraphApi._original_init = TelegraphApi.__init__
        TelegraphApi._original_method = TelegraphApi.method

    # Note: TelegraphApi uses __slots__, so we cannot attach new attributes to self.
    # We use the closure variable 'api_url' directly.
    # This means the patch is global for the process life-time (or until patched again).

    def patched_method(self, method, values=None, path=''):
        values = values.copy() if values is not None else {}

        if 'access_token' not in values and self.access_token:
            values['access_token'] = self.access_token

        # Use custom API URL from closure
        base_url = api_url.rstrip('/')
        url = f'{base_url}/{method}'
        if path:
             url = f'{base_url}/{method}/{path}'
             
        response = self.session.post(url, data=values).json()

        if response.get('ok'):
            return response['result']

        error = response.get('error')
        if isinstance(error, str) and error.startswith('FLOOD_WAIT_'):
            from telegraph.exceptions import RetryAfterError
            retry_after = int(error.rsplit('_', 1)[-1])
            raise RetryAfterError(retry_after)
        else:
            from telegraph.exceptions import TelegraphException
            raise TelegraphException(error)

    # We don't need to patch __init__ anymore
    TelegraphApi.method = patched_method


class TelegraphPublisher(IPublisher):
    """
    Main interface for publishing content to Telegraph.
    """
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}

    # Markdown inline image refs: `![alt](src)`. Alt may be empty; src stops at
    # the first ')'. Remote/data refs are left alone by _upload_markdown_local_images.
    MARKDOWN_LOCAL_IMG_RE = re.compile(r'!\[([^\]\n]*)\]\(([^)]+)\)')

    def __init__(
        self, 
        token: Optional[str] = None, 
        short_name: str = "TelegraphPublisher", 
        skip_duplicate: bool = True,
        image_size_limit: Optional[float] = None,
        auto_compress: bool = True,
        api_url: Optional[str] = None
    ):
        if api_url:
            _patch_telegraph_api(api_url)

        self.auth = TelegraphAuth()
        self.client = self.auth.get_client(token, short_name)
        self.converter = NovelMarkdownRenderer()
        self.skip_duplicate = skip_duplicate
        self._cache = _load_cache() if skip_duplicate else {}
        self.auto_compress = auto_compress

        # Determine image size limit and max workers
        if image_size_limit is not None:
            self.max_image_size = int(image_size_limit * 1024 * 1024)
            max_workers = 4  # Default
        else:
            config = load_config()
            # Check config for limit (in MB)
            config_limit = config.get('image_host', {}).get('max_size_mb')
            if config_limit:
                 self.max_image_size = int(float(config_limit) * 1024 * 1024)
            else:
                 self.max_image_size = MAX_IMAGE_SIZE
            
            # Check config for max_workers
            config_workers = config.get('image_host', {}).get('max_workers')
            max_workers = int(config_workers) if config_workers else 4

        # Image hosts may require credentials or optional dependencies.  Text-only
        # publishing should not pay that initialization cost (or require an image
        # host configuration), so create the uploader only when it is first used.
        self._max_workers = max_workers
        self._uploader = None

    @property
    def uploader(self) -> ImageUploader:
        """Return the lazily initialized image uploader."""
        if self._uploader is None:
            self._uploader = ImageUploader(max_workers=self._max_workers)
        return self._uploader

    @uploader.setter
    def uploader(self, value: ImageUploader):
        """Allow callers to inject a configured or test uploader."""
        self._uploader = value

    def publish(
        self,
        file_path: str,
        title: Optional[str] = None,
        author_name: Optional[str] = None,
        author_url: Optional[str] = None,
    ) -> str:
        """
        Publishes a file (md, txt, image, zip) to Telegraph.
        
        Supported formats:
        - Text: .txt, .md, .markdown, .rst, .text
        - Images: .jpg, .jpeg, .png, .gif, .webp, .bmp
        - Archives: .zip (containing images)
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValidationError: If file type not supported or file too large
        """
        author_kwargs = _author_metadata_kwargs(author_name, author_url)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Reject unexpectedly large inputs before reading or extracting them.
        validate_file_size(file_path, 2048 * 1024 * 1024, "File too large")

        file_name = os.path.basename(file_path)
        if not title:
            title = os.path.splitext(file_name)[0]
        ext = os.path.splitext(file_name)[1].lower()
        
        # Validate file type and route to appropriate handler
        if ext in ALLOWED_ARCHIVE_EXTENSIONS:
            return self.publish_zip_gallery(file_path, title, **author_kwargs)
        elif ext in self.IMAGE_EXTENSIONS:
            return self.publish_image(file_path, title, **author_kwargs)
        elif ext in ALLOWED_TEXT_EXTENSIONS:
            return self.publish_markdown(file_path, title, **author_kwargs)
        else:
            # Unsupported file type
            supported = sorted(ALLOWED_TEXT_EXTENSIONS | self.IMAGE_EXTENSIONS | ALLOWED_ARCHIVE_EXTENSIONS)
            raise ValidationError(
                f"Unsupported file type: '{ext}'. "
                f"Supported formats: {', '.join(supported)}"
            )

    def _upload_markdown_local_images(self, content: str, base_dir: str):
        """
        Upload local images referenced by markdown and substitute remote URLs.

        Only filesystem paths that exist are uploaded; remote (http/https),
        data: and protocol-relative refs are passed through unchanged so this
        is also safe as a generic markdown prettifier. Partial upload failures
        are non-fatal: the failed ref keeps its original src (the page still
        publishes) and a short diagnostic is printed so the operator can see
        exactly which asset failed.

        Returns ``(content, assets)`` where ``assets`` is a list of
        ``{local, remote, status}`` dicts covering every local image the
        markdown referenced (``uploaded`` / ``failed``).
        """
        local_paths = []
        for _, src in self.MARKDOWN_LOCAL_IMG_RE.findall(content):
            src = src.strip()
            if src.startswith(('http://', 'https://', '//', 'data:')):
                continue
            path = os.path.normpath(os.path.join(base_dir, src))
            if os.path.isfile(path):
                local_paths.append(path)

        if not local_paths:
            return content, []

        batch = self.uploader.upload_batch(local_paths, max_size=self.max_image_size)
        url_map = batch.get_url_map()
        failed = batch.get_failed_paths()
        if failed:
            print(
                f"Warning: {len(failed)} markdown image(s) failed to upload; "
                f"keeping original refs: {failed}",
                flush=True,
            )

        assets = []
        for path in local_paths:
            url = url_map.get(path)
            assets.append({
                'local': os.path.relpath(path, base_dir).replace(os.sep, '/'),
                'remote': url,
                'status': 'uploaded' if url else 'failed',
            })

        def _replace(match) -> str:
            src = match.group(2).strip()
            if src.startswith(('http://', 'https://', '//', 'data:')):
                return match.group(0)
            path = os.path.normpath(os.path.join(base_dir, src))
            url = url_map.get(path)
            return f'![{match.group(1)}]({url})' if url else match.group(0)

        return self.MARKDOWN_LOCAL_IMG_RE.sub(_replace, content), assets

    def _link_pages(
        self,
        pages_info: List[Dict],
        author_name: Optional[str] = None,
        author_url: Optional[str] = None,
    ):
        """
        Helper to add navigation links (Prev/Next/Index) to a list of pages.
        Robust: retries on failure, verifies links are correct.
        """
        author_kwargs = _author_metadata_kwargs(author_name, author_url)
        total_parts = len(pages_info)
        if total_parts <= 1:
            return

        print(f"Linking {total_parts} pages...", end="", flush=True)
        failed_links = []
        
        for i, info in enumerate(pages_info):
            # Show progress every 10 pages
            if (i + 1) % 10 == 0:
                print(f" {i+1}", end="", flush=True)
            nav_nodes = []
            
            # 1. Navigation Links (Prev/Next) - only link to valid pages
            nav_links = []
            if i > 0:
                prev_url = pages_info[i-1]['url']
                nav_links.append({
                    'tag': 'a',
                    'attrs': {'href': prev_url},
                    'children': [f'◀ Previous / 上一页']
                })
                nav_links.append(" | ")
            
            if i < total_parts - 1:
                next_url = pages_info[i+1]['url']
                nav_links.append({
                    'tag': 'a',
                    'attrs': {'href': next_url},
                    'children': [f'Next / 下一页 ▶']
                })
            
            if nav_links:
                nav_nodes.append({'tag': 'p', 'children': nav_links})
            
            # 2. Pagination Index - only include successfully published pages
            page_index_nodes = ["Pages: "]
            
            if total_parts < 50:
                for p_idx, p_info in enumerate(pages_info):
                    label = str(p_info.get('part_num', p_idx + 1))
                    if p_idx == i:
                        page_index_nodes.append({'tag': 'b', 'children': [f"[{label}]"]})
                    else:
                        page_index_nodes.append({'tag': 'a', 'attrs': {'href': p_info['url']}, 'children': [f"[{label}]"]})
                    page_index_nodes.append(" ")
            else:
                page_index_nodes.append(f"{info.get('part_num', i+1)} / {total_parts}")

            nav_nodes.append({'tag': 'p', 'children': page_index_nodes})

            if nav_nodes:
                new_content = info['content'] + [{'tag': 'hr'}] + nav_nodes
                if _node_json_size(new_content) > TELEGRAPH_CONTENT_LIMIT:
                    # Long titles/URLs can make the full page index larger than
                    # the reserved space. Keep Prev/Next and a compact index.
                    nav_nodes[-1] = {
                        'tag': 'p',
                        'children': [f"Pages: {info.get('part_num', i+1)} / {total_parts}"],
                    }
                    new_content = info['content'] + [{'tag': 'hr'}] + nav_nodes
                if _node_json_size(new_content) > TELEGRAPH_CONTENT_LIMIT:
                    raise ValidationError("Telegraph page navigation exceeds the content limit")
                
                # Retry logic for linking
                max_retries = 3
                success = False
                for attempt in range(max_retries):
                    try:
                        self.client.edit_page(
                            path=info['path'],
                            title=info['title'],
                            content=new_content,
                            **author_kwargs,
                        )
                        success = True
                        break
                    except Exception as e:
                        error_msg = str(e)
                        if 'CONTENT_TOO_BIG' in error_msg:
                            raise ValidationError("Telegraph page navigation exceeds the content limit") from e
                        match = re.search(r'Retry in (\d+)', error_msg)
                        if 'Flood control' in error_msg and match:
                            wait_time = int(match.group(1)) + 1
                            time.sleep(wait_time)
                        elif attempt < max_retries - 1:
                            time.sleep(1)
                        else:
                            failed_links.append(i + 1)
                            print(f"Warning: Failed to link Part {i+1}: {e}")
                
                if success and i < total_parts - 1:
                    time.sleep(0.3)  # Small delay between edits
        
        print()  # End the progress line
        if failed_links:
            print(f"Note: Navigation failed for parts: {failed_links}. Content is still accessible.")

    def publish_markdown(
        self,
        file_path: str,
        title: str,
        author_name: Optional[str] = None,
        author_url: Optional[str] = None,
    ) -> str:
        """
        Publish a markdown/text file to Telegraph.
        Large files are automatically split into multiple pages.
        
        Pages are bounded by rendered UTF-8 JSON size, without truncating text.
        """
        author_kwargs = _author_metadata_kwargs(author_name, author_url)

        # Validate file can be read as text
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            raise ValidationError(
                f"Cannot read file as text. File may be binary (PDF, DOCX, etc.). "
                f"Only plain text files (.txt, .md) are supported."
            )
        
        # Check for empty content
        if not content.strip():
            raise ValidationError("File is empty or contains only whitespace")
        
        # Generate content key for deduplication
        content_key = None
        if self.skip_duplicate:
            cache_material = content + title
            if author_name is not None or author_url is not None:
                cache_material += f"\0{author_name!r}\0{author_url!r}"
            content_key = _content_hash(cache_material)
        
        # Check for duplicate content
        if content_key and content_key in self._cache:
            cached_url = self._cache[content_key]
            print(f"Skipping duplicate content, already published: {cached_url}")
            return cached_url
        
        # Rich-media Phase 1: upload any local filesystem-referenced images
        # (Catbox / configured ImageUploader) and swap the markdown refs to
        # their remote URLs BEFORE conversion so Telegraph renders inline
        # images in source order. Pure-text (no local image refs) is untouched.
        content, _ = self._upload_markdown_local_images(
            content, os.path.dirname(os.path.abspath(file_path))
        )

        # Keep the source target, then enforce the actual rendered byte budget.
        # A 20k-character Chinese novel with many short paragraphs can exceed
        # Telegraph's 64 KiB limit despite fitting the source target.
        if len(content) > MARKDOWN_PAGE_CHUNK_SIZE:
            print(f"Text too large ({len(content)} chars). Splitting...")
        chunks = _split_markdown_chunks(content)
        node_pages = [
            page for chunk in chunks
            for page in _paginate_nodes(self.converter.convert(chunk))
        ]

        total_parts = len(node_pages)
        pages_info = []
        
        for i, nodes in enumerate(node_pages):
            part_num = i + 1
            page_title = title
            if total_parts > 1:
                page_title = f"{title} ({part_num}/{total_parts})"
            
            print(f"Publishing Part {part_num}/{total_parts} ({_node_json_size(nodes)} bytes)...")
            
            # Retry with delay for flood control
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    response = self.client.create_page(
                        title=page_title,
                        content=nodes,
                        **author_kwargs,
                    )
                    pages_info.append({
                        'path': response['path'],
                        'url': response['url'],
                        'title': page_title,
                        'content': nodes,
                        'part_num': part_num
                    })
                    # Small delay between requests to avoid flood control
                    if i < total_parts - 1:
                        time.sleep(0.5)
                    break
                except Exception as e:
                    error_msg = str(e)
                    if 'CONTENT_TOO_BIG' in error_msg:
                        raise ValidationError(
                            f"Telegraph rejected Part {part_num}/{total_parts}: CONTENT_TOO_BIG"
                        ) from e
                    # Check if max retries reached
                    if attempt >= max_retries - 1:
                        raise RuntimeError(
                            f"Failed to publish Part {part_num}/{total_parts} after {max_retries} attempts: {e}\n"
                            f"Successfully published: {len(pages_info)} pages. First page: {pages_info[0]['url'] if pages_info else 'none'}"
                        )
                    # Handle flood control - extract wait time
                    match = re.search(r'Retry in (\d+)', error_msg)
                    if 'Flood control' in error_msg and match:
                        wait_time = int(match.group(1)) + 1
                        print(f"  Waiting {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        time.sleep(2)

        # Link pages if multiple
        self._link_pages(
            pages_info,
            author_name=author_name,
            author_url=author_url,
        )

        result_url = pages_info[0]['url'] if pages_info else ""
        
        # Save to cache for deduplication
        if content_key and result_url:
            self._cache[content_key] = result_url
            _save_cache(self._cache)
        
        return result_url

    def _apply_proxy_manifest(self, content: str, manifest) -> tuple:
        """Rewrite markdown image refs that a manifest maps to a media proxy URL.

        Returns ``(content, assets)`` where ``assets`` contains one
        ``{local, remote, status: 'proxied'}`` entry per successful rewrite.
        Manifest entries without a usable proxy URL are ignored and continue to
        the normal image-host upload path.
        """
        if not manifest:
            return content, []
        proxied = {}
        with_source = 0
        for entry in manifest:
            ref = reference_from_entry(entry)
            if not ref or not ref.source_url:
                continue
            with_source += 1
            url = media_proxy_url(ref.source_url)
            if url:
                local = os.path.normpath(ref.local_ref).replace(os.sep, "/")
                proxied[local] = (url, ref.asset_id)

        if not proxied:
            if with_source:
                # Loud, never silent: a manifest with real sources that proxies
                # to nothing means every inline image will reach Telegraph as a
                # relative ref and be silently dropped (text-only page). This
                # almost always means TELEPRESS_MEDIA_PROXY_BASE /
                # TELEPRESS_MEDIA_PROXY_HOSTS are missing in this runtime while
                # the caller believes proxying is configured.
                print(
                    f"Warning: rich-novel manifest carries {with_source} image "
                    "source(s) but none were proxied — check "
                    "TELEPRESS_MEDIA_PROXY_BASE / TELEPRESS_MEDIA_PROXY_HOSTS "
                    "configuration; inline images may be dropped by Telegraph",
                    flush=True,
                )
            return content, []

        assets = []

        def _replace(match) -> str:
            src = match.group(2).strip()
            if src.startswith(("http://", "https://", "//", "data:")):
                return match.group(0)
            rel = os.path.normpath(src).replace(os.sep, "/")
            hit = proxied.get(rel)
            if not hit:
                return match.group(0)
            url, asset_id = hit
            asset = {"local": rel, "remote": url, "status": "proxied"}
            if asset_id:
                asset["assetId"] = asset_id
            assets.append(asset)
            return f"![{match.group(1)}]({url})"

        return self.MARKDOWN_LOCAL_IMG_RE.sub(_replace, content), assets

    def publish_rich_markdown(
        self,
        file_path: str,
        title: str,
        manifest=None,
        author_name: Optional[str] = None,
        author_url: Optional[str] = None,
    ) -> Dict:
        """
        Publish a rich-novel markdown file with local image assets.

        Unlike :meth:`publish_markdown` (which uploads local refs and returns a
        plain URL), this returns ``{url, assets: [{local, remote, status}]}`` so
        the caller can prove which local images were uploaded and which failed.
        The publishing itself reuses :meth:`publish_markdown` by first rewriting
        local image refs to remote URLs, so pagination/deduplication behaviour is
        identical to the existing rich-markdown path.

        ``manifest`` is optional: a list of ``{"local": "<md rel path>",
        "source": "<original CDN URL>"}``. When a media proxy is configured
        (``TELEPRESS_MEDIA_PROXY_BASE`` + ``TELEPRESS_MEDIA_PROXY_HOSTS``, or the
        legacy ``TELEPRESS_PIXIV_PROXY_BASE`` alias), matching hosts are rewritten
        to the proxy and reported as ``status: "proxied"`` instead of being uploaded.
        """
        author_kwargs = _author_metadata_kwargs(author_name, author_url)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            raise ValidationError("Cannot read markdown as text")

        if not content.strip():
            raise ValidationError("File is empty or contains only whitespace")

        content, proxy_assets = self._apply_proxy_manifest(content, manifest)
        content, uploaded_assets = self._upload_markdown_local_images(
            content, os.path.dirname(os.path.abspath(file_path))
        )
        assets = proxy_assets + uploaded_assets

        fd, tmp_path = tempfile.mkstemp(suffix='.md', prefix='telepress-rich-')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
            url = self.publish_markdown(tmp_path, title, **author_kwargs)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        return {'url': url, 'assets': assets}


    def publish_image(
        self,
        image_path: str,
        title: str,
        author_name: Optional[str] = None,
        author_url: Optional[str] = None,
    ) -> str:
        """Publish a single image to Telegraph."""
        author_kwargs = _author_metadata_kwargs(author_name, author_url)
        url = self.uploader.upload(
            image_path,
            auto_compress=self.auto_compress,
            max_size=self.max_image_size
        )
        content = [{'tag': 'img', 'attrs': {'src': url}}]
        response = self.client.create_page(
            title=title,
            content=content,
            **author_kwargs,
        )
        return response['url']

    def publish_text(
        self,
        content: str,
        title: str,
        author_name: Optional[str] = None,
        author_url: Optional[str] = None,
    ) -> str:
        """
        Publish text/markdown content directly to Telegraph.
        
        This is useful for programmatic publishing without creating a temp file.
        
        Args:
            content: Markdown or plain text content
            title: Page title
        
        Returns:
            str: URL of the published Telegraph page
        
        Example:
            >>> publisher = TelegraphPublisher()
            >>> url = publisher.publish_text("# Hello\n\nWorld!", title="Test")
        """
        author_kwargs = _author_metadata_kwargs(author_name, author_url)

        import tempfile
        import os
        
        # Write content to temp file and use existing publish_markdown logic
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(content)
            tmp_path = f.name
        
        try:
            return self.publish_markdown(tmp_path, title, **author_kwargs)
        finally:
            os.unlink(tmp_path)

    def publish_zip_gallery(
        self,
        zip_path: str,
        title: str,
        footer_nodes: Optional[List[Dict]] = None,
        author_name: Optional[str] = None,
        author_url: Optional[str] = None,
    ) -> str:
        """
        Publish a zip file containing images as a gallery.
        
        Args:
            zip_path: Path to a zip file containing the gallery images.
            title: Page title (shared by all pages when paginated).
            footer_nodes: Optional extra Telegraph nodes (tags, source link,
                warnings) appended to the first page only, above the
                Prev/Next navigation links.
        
        Limits:
        - Maximum 5000 images (50 pages × 100 images)
        - Images exceeding this will be truncated with a warning
        """
        author_kwargs = _author_metadata_kwargs(author_name, author_url)

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                safe_extract_zip(zip_path, temp_dir)
            except zipfile.BadZipFile:
                raise ValidationError("Invalid zip file")

            images = []
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if os.path.splitext(file)[1].lower() in self.IMAGE_EXTENSIONS:
                        images.append(os.path.join(root, file))
            
            images.sort(key=lambda x: natural_sort_key(os.path.basename(x)))
            
            if not images:
                raise ValidationError("No images found in zip file")
            
            # Pagination logic
            chunk_size = MAX_IMAGES_PER_PAGE
            chunks = [images[i:i + chunk_size] for i in range(0, len(images), chunk_size)]
            total_parts = len(chunks)
            
            if total_parts > 1:
                print(f"Gallery has {len(images)} images. Splitting into {total_parts} pages.")
            
            # Two-pass approach to support Prev/Next links
            # Pass 1: Create all pages
            pages_info = [] # Stores {'path': str, 'url': str, 'title': str, 'content': list}
            
            for i, chunk_images in enumerate(chunks):
                part_num = i + 1
                page_title = title
                if total_parts > 1:
                    page_title = f"{title} ({part_num}/{total_parts})"
                
                print(f"Uploading Part {part_num}/{total_parts} ({len(chunk_images)} images)...")
                
                # Use batch upload with progress bar
                def progress_callback(completed, total, result):
                    percent = (completed / total) * 100
                    bar_length = 30
                    filled_length = int(bar_length * completed // total)
                    bar = '█' * filled_length + '-' * (bar_length - filled_length)
                    sys.stdout.write(f'\rProgress: |{bar}| {percent:.1f}% ({completed}/{total})')
                    sys.stdout.flush()
                
                batch_result = self.uploader.upload_batch(
                    chunk_images,
                    auto_compress=self.auto_compress,
                    max_size=self.max_image_size,
                    progress_callback=progress_callback
                )
                print()  # Newline after progress bar
                
                url_map = batch_result.get_url_map()
                failed_paths = batch_result.get_failed_paths()
                
                if failed_paths:
                    print(f"Warning: {len(failed_paths)} images failed to upload.")
                    for p in failed_paths:
                         # Find the specific result for error message
                        err = next((r.error for r in batch_result.results if r.path == p), "Unknown error")
                        print(f"  - {os.path.basename(p)}: {err}")

                content = []
                for img_path in chunk_images:
                    if img_path in url_map:
                        content.append({'tag': 'img', 'attrs': {'src': url_map[img_path]}})

                # Footer metadata (tags / source link / warnings) belongs on the
                # first page only; later pages stay image-only plus navigation.
                if i == 0 and footer_nodes:
                    content = content + list(footer_nodes)
                
                if not content and len(chunk_images) > 0:
                     print(f"Warning: Part {part_num} resulted in empty content.")


                try:
                    # Create initial page
                    response = self.client.create_page(
                        title=page_title,
                        html_content=None,
                        content=content if content else [{'tag': 'p', 'children': ['(Empty Page)']}],
                        **author_kwargs,
                    )
                    pages_info.append({
                        'path': response['path'],
                        'url': response['url'],
                        'title': page_title,
                        'content': content
                    })
                except Exception as e:
                    raise RuntimeError(f"Failed to publish Part {part_num}: {e}")

            # Pass 2: Update pages with navigation
            self._link_pages(
                pages_info,
                author_name=author_name,
                author_url=author_url,
            )

            return pages_info[0]['url'] if pages_info else ""

    def publish_optimized_gallery(
        self,
        image_urls: List[str],
        title: str,
        footer_nodes: Optional[List[Dict]] = None,
        author_name: Optional[str] = None,
        author_url: Optional[str] = None,
    ) -> str:
        """
        Publish a gallery using existing image URLs (no upload needed).
        Handles pagination and navigation linking automatically.
        
        Args:
            image_urls: Public image URLs to render in the gallery.
            title: Page title (shared by all pages when paginated).
            footer_nodes: Optional extra Telegraph nodes (tags, source link,
                warnings) appended to the first page only, above the
                Prev/Next navigation links.
        """
        author_kwargs = _author_metadata_kwargs(author_name, author_url)

        if not image_urls:
            raise ValidationError("No image URLs provided")
        
        # Pagination logic
        chunk_size = MAX_IMAGES_PER_PAGE
        chunks = [image_urls[i:i + chunk_size] for i in range(0, len(image_urls), chunk_size)]
        total_parts = len(chunks)
        
        if total_parts > 1:
            print(f"Gallery has {len(image_urls)} images. Splitting into {total_parts} pages.")
        
        # Two-pass approach to support Prev/Next links
        pages_info = [] 
        
        for i, chunk_urls in enumerate(chunks):
            part_num = i + 1
            page_title = title
            if total_parts > 1:
                page_title = f"{title} ({part_num}/{total_parts})"
            
            print(f"Creating Part {part_num}/{total_parts} ({len(chunk_urls)} images)...")
            
            content = []
            for url in chunk_urls:
                content.append({'tag': 'img', 'attrs': {'src': url}})

            # Footer metadata (tags / source link / warnings) belongs on the
            # first page only; later pages stay image-only plus navigation.
            if i == 0 and footer_nodes:
                content = content + list(footer_nodes)
            
            try:
                # Create initial page
                response = self.client.create_page(
                    title=page_title,
                    html_content=None,
                    content=content if content else [{'tag': 'p', 'children': ['(Empty Page)']}],
                    **author_kwargs,
                )
                pages_info.append({
                    'path': response['path'],
                    'url': response['url'],
                    'title': page_title,
                    'content': content
                })
            except Exception as e:
                raise RuntimeError(f"Failed to publish Part {part_num}: {e}")

        # Link pages
        self._link_pages(
            pages_info,
            author_name=author_name,
            author_url=author_url,
        )

        return pages_info[0]['url'] if pages_info else ""
