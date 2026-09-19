from unittest import TestCase
from unittest.mock import patch

from telepress.pixiv_proxy import pixiv_proxy_url, reference_from_entry


class TestReferenceFromEntry(TestCase):
    def test_accepts_new_sourceUrl_and_assetId_shape(self):
        ref = reference_from_entry({
            "local": "images/001.jpg",
            "assetId": "pixiv:123:pixivimage:p0",
            "sourceUrl": "https://i.pximg.net/img-master/img/1_p0.jpg",
        })
        self.assertEqual(ref.local_ref, "images/001.jpg")
        self.assertEqual(ref.asset_id, "pixiv:123:pixivimage:p0")
        self.assertEqual(ref.source_url, "https://i.pximg.net/img-master/img/1_p0.jpg")

    def test_falls_back_to_legacy_local_and_source(self):
        ref = reference_from_entry({
            "local": "images/001.jpg",
            "source": "https://i.pximg.net/x.jpg",
        })
        self.assertEqual(ref.local_ref, "images/001.jpg")
        self.assertEqual(ref.source_url, "https://i.pximg.net/x.jpg")
        self.assertIsNone(ref.asset_id)

    def test_requires_local_ref(self):
        self.assertIsNone(reference_from_entry({"source": "https://i.pximg.net/x.jpg"}))


class TestPixivProxyUrl(TestCase):
    def test_no_proxy_disabled(self):
        with patch.dict(
            "telepress.pixiv_proxy.os.environ",
            {"TELEPRESS_PIXIV_PROXY_BASE": ""},
        ):
            self.assertIsNone(pixiv_proxy_url("https://i.pximg.net/img.png"))

    def test_rewrites_pixiv_cdn(self):
        with patch.dict(
            "telepress.pixiv_proxy.os.environ",
            {"TELEPRESS_PIXIV_PROXY_BASE": "https://media.example.com"},
        ):
            self.assertEqual(
                pixiv_proxy_url("https://i.pximg.net/c/300x300/img-master/img/1234_p0.jpg"),
                "https://media.example.com/pixiv/c/300x300/img-master/img/1234_p0.jpg",
            )

    def test_preserves_query(self):
        with patch.dict(
            "telepress.pixiv_proxy.os.environ",
            {"TELEPRESS_PIXIV_PROXY_BASE": "https://media.example.com/"},
        ):
            self.assertEqual(
                pixiv_proxy_url("https://i.pximg.net/img-master/img/1.png?format=webp"),
                "https://media.example.com/pixiv/img-master/img/1.png?format=webp",
            )

    def test_rejects_other_upstreams(self):
        with patch.dict(
            "telepress.pixiv_proxy.os.environ",
            {"TELEPRESS_PIXIV_PROXY_BASE": "https://media.example.com"},
        ):
            self.assertIsNone(pixiv_proxy_url("https://i.imgur.com/x.png"))
            self.assertIsNone(pixiv_proxy_url("http://i.pximg.net/x.png"))
            self.assertIsNone(pixiv_proxy_url("https://i.pximg.net.example/x.png"))
            self.assertIsNone(pixiv_proxy_url(""))
