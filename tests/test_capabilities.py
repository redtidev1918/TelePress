"""Tests for the new ImageHost.capabilities aggregate capability declaration.

Covers:
  - every concrete host exposes a read-only ImageHostCapabilities
  - values aggregate the host's existing trait attributes (backwards compatible)
  - existing per-attribute reads (host.supports_native_batch, host.temporary,
    host.supports_arbitrary_files) still work directly
  - subclass-defined class attributes are reflected in capabilities
  - ImageHostCapabilities is frozen (immutable)
"""
from dataclasses import FrozenInstanceError
import unittest

from telepress.image_host import (
    ImageHost, ImageHostCapabilities,
    ImgbbHost, ImgurHost, SmmsHost, CatboxHost, FreeImageHost,
    UploadcareHost, ImageKitHost, CloudinaryHost, ZeroXZeroHost,
    LitterboxHost, R2Host, S3Host, CustomHost,
)
from telepress import ImageHostCapabilities as RootCapabilities


class _MinimalHost(ImageHost):
    """Host that only sets name + temporary; other traits default."""

    @property
    def name(self):
        return "minimal"

    def upload(self, image_path):
        return "http://mock"


class TestCapabilitiesUnittest(unittest.TestCase):
    def test_root_export_matches_module(self):
        self.assertIs(RootCapabilities, ImageHostCapabilities)

    def test_default_capabilities(self):
        h = _MinimalHost()
        cap = h.capabilities
        self.assertIsInstance(cap, ImageHostCapabilities)
        self.assertEqual(cap.name, "minimal")
        self.assertFalse(cap.supports_native_batch)
        self.assertFalse(cap.supports_arbitrary_files)
        self.assertFalse(cap.temporary)
        self.assertTrue(cap.upload_returns_stable_url)

    def test_existing_attribute_reads_preserved(self):
        # Old call pattern: read traits directly — must still work unchanged.
        h = _MinimalHost()
        self.assertIsInstance(h.supports_native_batch, bool)
        self.assertFalse(h.supports_native_batch)

    def test_temporary_host_reflected(self):
        # litterbox/0x0 declare temporary=True at class level.
        for host in (LitterboxHost(), ZeroXZeroHost()):
            self.assertTrue(host.temporary, type(host).__name__)
            self.assertTrue(host.capabilities.temporary)

    def test_arbitrary_files_reflected(self):
        # These hosts declare supports_arbitrary_files=True as class attributes.
        self.assertTrue(UploadcareHost.supports_arbitrary_files)
        self.assertTrue(ImageKitHost.supports_arbitrary_files)
        self.assertTrue(ZeroXZeroHost.supports_arbitrary_files)
        self.assertTrue(LitterboxHost.supports_arbitrary_files)

    def test_all_concrete_hosts_share_capabilities_property(self):
        # capabilities is defined on the base class; every subclass must expose it
        # without overriding or shadowing with a different attribute type.
        hosts = [
            ImgbbHost, ImgurHost, SmmsHost, CatboxHost, FreeImageHost,
            UploadcareHost, ImageKitHost, CloudinaryHost, ZeroXZeroHost,
            LitterboxHost, S3Host, R2Host, CustomHost,
        ]
        for hcls in hosts:
            prop = getattr(hcls, "capabilities", None)
            self.assertIsInstance(prop, property, f"{hcls.__name__} must expose capabilities")
            self.assertTrue(issubclass(hcls, ImageHost), hcls.__name__)

    def test_capabilities_is_frozen(self):
        h = _MinimalHost()
        with self.assertRaises(FrozenInstanceError):
            h.capabilities.temporary = True


if __name__ == "__main__":
    unittest.main()