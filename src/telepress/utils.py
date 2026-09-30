import re
import os
import zipfile
from typing import List, Dict, Union, Tuple
from .exceptions import SecurityError, ValidationError, ConversionError

# Constants for limits
MAX_TEXT_SIZE = 60 * 1024  # ~60KB safe limit for text content per page
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB limit per image (Telegraph hard limit)
MAX_IMAGES_PER_PAGE = 100  # Images per page to avoid browser performance issues
# No artificial limits on pages/total images - let Telegraph's rate limiting handle it
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
ALLOWED_TEXT_EXTENSIONS = {'.txt', '.md', '.markdown', '.rst', '.text'}
ALLOWED_ARCHIVE_EXTENSIONS = {'.zip'}

def natural_sort_key(s: str) -> List[Union[int, str]]:
    """
    Sorts strings containing numbers naturally.
    e.g. ['1.png', '10.png', '2.png'] -> ['1.png', '2.png', '10.png']
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def validate_file_size(path: str, max_size: int, error_msg: str):
    """Checks if file size is within limits."""
    if os.path.getsize(path) > max_size:
        raise ValidationError(f"{error_msg} (Size: {os.path.getsize(path)/1024/1024:.2f}MB, Max: {max_size/1024/1024}MB)")

def safe_extract_zip(zip_path: str, extract_to: str):
    """
    Safely extracts a zip file, preventing Zip Slip vulnerabilities.
    """
    with zipfile.ZipFile(zip_path, 'r') as zf:
        abs_target_path = os.path.abspath(extract_to)
        for member in zf.namelist():
            # Resolve the path to ensure it doesn't escape the target directory
            member_path = os.path.join(extract_to, member)
            abs_member_path = os.path.abspath(member_path)

            # commonpath compares complete path components; a string prefix
            # check would incorrectly allow a sibling such as /tmp/outside.
            try:
                is_inside_target = os.path.commonpath(
                    [abs_target_path, abs_member_path]
                ) == abs_target_path
            except ValueError:
                is_inside_target = False

            if not is_inside_target:
                raise SecurityError(f"Zip Slip attempt detected: {member}")
            
            # Extract only if safe
            zf.extract(member, extract_to)

def sanitize_nodes(nodes: List[Dict]) -> List[Dict]:
    """
    Recursively downgrades headers h1->h3, h2->h4 because Telegraph
    only supports h3 and h4.
    """
    if not isinstance(nodes, list):
        return nodes
    
    for node in nodes:
        if isinstance(node, dict):
            tag = node.get('tag')
            if tag == 'h1':
                node['tag'] = 'h3'
            elif tag == 'h2':
                node['tag'] = 'h4'
            elif tag in ['h5', 'h6']:
                node['tag'] = 'h4'
            
            if 'children' in node:
                sanitize_nodes(node['children'])
    return nodes


# Formats that support compression
COMPRESSIBLE_FORMATS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}
SKIP_COMPRESSION_FORMATS = {'.gif'}  # Animated, complex to handle


def compress_image_to_size(
    image_path: str,
    max_size: int = MAX_IMAGE_SIZE,
    min_quality: int = 30,
    min_scale: float = 0.3,
    prefer_webp: bool = False
) -> Tuple[str, bool]:
    """
    Compress an image to fit within max_size bytes.

    Production path uses a demand-driven libvips (pyvips) pipeline so the full
    source image is never materialized in Python memory.  Supports: JPEG, PNG,
    WebP, BMP, TIFF formats.

    Strategy (prioritizing quality):
    1. Compute a "safe" candidate edge (long edge <= 4096 px, <= 16 MP).
    2. Run a logarithmic quality search (95 -> min_quality) at that edge.
    3. If still too large, progressively scale down (0.9 .. min_scale).
    4. Runs on JPEG, or WebP when prefer_webp=True.

    Args:
        image_path: Path to the source image
        max_size: Maximum file size in bytes (default: 5MB)
        min_quality: Minimum quality to try before scaling (default: 30)
        min_scale: Minimum scale factor before giving up (default: 0.3)
        prefer_webp: Use WebP output format instead of JPEG (default: False)

    Returns:
        Tuple of (output_path, was_compressed):
        - output_path: Path to the (possibly compressed) image
        - was_compressed: True if compression was applied

    Raises:
        ConversionError: If unable to compress to target size or if the image
            cannot be decoded/encoded by libvips.
    """
    from .vips import compress_image_to_size as _vips_compress
    return _vips_compress(
        image_path,
        max_size=max_size,
        min_quality=min_quality,
        min_scale=min_scale,
        prefer_webp=prefer_webp,
    )
