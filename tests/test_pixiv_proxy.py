from unittest import TestCase
from unittest.mock import patch

from telepress.pixiv_proxy import pixiv_proxy_url


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
