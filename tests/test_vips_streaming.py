"""Streaming (libvips/pyvips) compression regression tests.

These cover the production path of :func:`compress_image_to_size`, which must
never materialize the full source image in Python memory.  The large-source
fixture is built lazily with pyvips itself (black + constant), so it does not
require generating a huge NumPy array in the test process.

Note: the pyvips self-contained binary does not ship a BMP *saver*, so the big
fixture uses an uncompressed TIFF (100% pure RGB, already listed in
``COMPRESSIBLE_FORMATS``) instead; ``thumbnail`` loads it identically to a BMP.
"""
import os
import tempfile
import unittest

import pyvips

from telepress import compress_image_to_size, MAX_IMAGE_SIZE
from telepress.exceptions import ConversionError
from telepress import vips as vips_module


class TestVipsStreamingBigImage(unittest.TestCase):
    def test_large_image_is_streamed_and_bounded(self):
        """A 5000x7000 source compresses to <= 5MB and long edge <= 4096."""
        source = tempfile.mktemp(suffix='.tiff')
        try:
            image = pyvips.Image.black(5000, 7000, bands=3) + 127
            image.write_to_file(source)
            original_size = os.path.getsize(source)
            self.assertGreater(original_size, 5 * 1024 * 1024)

            out, compressed = compress_image_to_size(
                str(source), max_size=5 * 1024 * 1024)

            self.assertTrue(compressed)
            self.assertNotEqual(out, source)
            self.assertLessEqual(os.path.getsize(out), 5 * 1024 * 1024)

            decoded = pyvips.Image.new_from_file(out)
            self.assertLessEqual(max(decoded.width, decoded.height), 4096)
            decoded = None

            # Original file is untouched
            self.assertTrue(os.path.exists(source))
            self.assertEqual(os.path.getsize(source), original_size)
        finally:
            if os.path.exists(source):
                os.unlink(source)

    def test_no_temp_files_leak_on_impossible_target(self):
        """A target that can never fit raises ConversionError and cleans up."""
        source = tempfile.mktemp(suffix='.tiff')
        try:
            image = pyvips.Image.black(2000, 2000, bands=3) + 127
            image.write_to_file(source)
            before = set(os.listdir(tempfile.gettempdir()))
            with self.assertRaises(ConversionError) as ctx:
                compress_image_to_size(source, max_size=100)  # 100 bytes
            self.assertIn("Unable to compress", str(ctx.exception))
            after = set(os.listdir(tempfile.gettempdir()))
            # No telepress-* candidates left behind (allow unrelated noise by
            # filtering for our own prefix).
            leftovers = [f for f in (after - before)
                         if f.startswith('telepress-')]
            self.assertEqual(leftovers, [])
        finally:
            if os.path.exists(source):
                os.unlink(source)


class TestVipsStreamingFormats(unittest.TestCase):
    def test_small_image_returned_untouched(self):
        """Under-limit images are returned as-is with no temp file produced."""
        source = tempfile.mktemp(suffix='.jpg')
        try:
            from PIL import Image as PillowImage
            PillowImage.new('RGB', (100, 100), 'red').save(source, 'JPEG')

            out, compressed = compress_image_to_size(source, MAX_IMAGE_SIZE)
            self.assertEqual(out, source)
            self.assertFalse(compressed)
        finally:
            if os.path.exists(source):
                os.unlink(source)

    def test_gif_keeps_raising_conversion_error(self):
        """GIF is explicitly skipped and raises ConversionError."""
        source = tempfile.mktemp(suffix='.gif')
        try:
            from PIL import Image as PillowImage
            PillowImage.new('RGB', (100, 100), 'green').save(source, 'GIF')

            with self.assertRaises(ConversionError) as ctx:
                compress_image_to_size(source, max_size=10)
            self.assertIn("GIF", str(ctx.exception))
        finally:
            if os.path.exists(source):
                os.unlink(source)

    def test_rgba_is_flattened_for_jpeg(self):
        """A large RGBA source compresses to a JPEG with no alpha channel."""
        source = tempfile.mktemp(suffix='.png')
        try:
            import numpy as np
            from PIL import Image as PillowImage
            noise = np.random.randint(0, 255, (1200, 1200, 4), dtype=np.uint8)
            PillowImage.fromarray(noise, 'RGBA').save(source, 'PNG')
            original_size = os.path.getsize(source)
            max_size = min(original_size - 50000, 200000)

            out, compressed = compress_image_to_size(source, max_size)
            self.assertTrue(compressed)

            decoded = pyvips.Image.new_from_file(out)
            self.assertEqual(decoded.bands, 3)
            self.assertFalse(decoded.hasalpha())
            decoded = None
        finally:
            if os.path.exists(source):
                os.unlink(source)

    def test_webp_output_when_preferred(self):
        """prefer_webp=True produces a WebP file under the target limit."""
        source = tempfile.mktemp(suffix='.png')
        try:
            import numpy as np
            from PIL import Image as PillowImage
            noise = np.random.randint(0, 255, (1200, 1200, 4), dtype=np.uint8)
            PillowImage.fromarray(noise, 'RGBA').save(source, 'PNG')
            max_size = min(os.path.getsize(source) - 50000, 200000)

            out, compressed = compress_image_to_size(
                source, max_size, prefer_webp=True)
            self.assertTrue(compressed)
            self.assertEqual(os.path.splitext(out)[1], '.webp')
            self.assertLessEqual(os.path.getsize(out), max_size)
        finally:
            if os.path.exists(source):
                os.unlink(source)

    def test_corrupted_file_raises_conversion_error(self):
        """Undecodable files raise ConversionError, not a raw exception."""
        source = tempfile.mktemp(suffix='.jpg')
        try:
            with open(source, 'wb') as f:
                f.write(b'not a valid image data')
            with self.assertRaises(ConversionError):
                compress_image_to_size(source, max_size=10)
        finally:
            if os.path.exists(source):
                os.unlink(source)


class TestVipsQualitySearch(unittest.TestCase):
    def test_quality_search_uses_logarithmic_encodes(self):
        """The binary quality search is O(log N) encode attempts."""

        class FakeProbe:
            def __init__(self):
                self.calls = []

            def __call__(self, quality):
                self.calls.append(quality)
                return quality  # size grows with quality, max_size fixed

        probe = FakeProbe()
        best = vips_module._binary_search_quality(
            30, 95, probe, max_size=72)

        self.assertIsNotNone(best)
        self.assertEqual(best, 72)  # highest quality whose encode <= 72 bytes
        self.assertLessEqual(len(probe.calls), 7)  # ceiling(log2(66)) + 1

    def test_quality_search_none_when_nothing_fits(self):
        """If even the minimum quality exceeds max_size, return None."""
        probe = lambda quality: quality  # noqa: E731
        best = vips_module._binary_search_quality(30, 95, probe, max_size=10)
        self.assertIsNone(best)


if __name__ == '__main__':
    unittest.main()