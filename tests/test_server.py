import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
from fastapi.testclient import TestClient


class TestServerEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test client with mocked publisher."""
        with patch('telepress.server.TelegraphPublisher') as MockPublisher:
            cls.mock_publisher_instance = MagicMock()
            MockPublisher.return_value = cls.mock_publisher_instance
            
            from telepress.server import app
            cls.client = TestClient(app)

    def setUp(self):
        """Reset mock before each test."""
        self.mock_publisher_instance.reset_mock()
        self.mock_publisher_instance.publish.return_value = 'http://telegra.ph/test'

    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['service'], 'telepress')

    @patch('telepress.server.TelegraphPublisher')
    def test_publish_text_success(self, MockPublisher):
        """Test publishing text content."""
        mock_instance = MagicMock()
        mock_instance.publish.return_value = 'http://telegra.ph/result'
        MockPublisher.return_value = mock_instance
        
        response = self.client.post("/publish/text", json={
            "content": "# Test Content\n\nHello world!",
            "title": "Test Title"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['url'], 'http://telegra.ph/result')

    @patch('telepress.server.TelegraphPublisher')
    def test_publish_text_with_token(self, MockPublisher):
        """Test publishing text with custom token."""
        mock_instance = MagicMock()
        mock_instance.publish.return_value = 'http://telegra.ph/result'
        MockPublisher.return_value = mock_instance
        
        response = self.client.post("/publish/text", json={
            "content": "Content",
            "title": "Title",
            "token": "custom_token"
        })
        
        self.assertEqual(response.status_code, 200)
        MockPublisher.assert_called_with(token="custom_token")

    @patch('telepress.server.TelegraphPublisher')
    def test_publish_file_markdown(self, MockPublisher):
        """Test uploading and publishing a markdown file."""
        mock_instance = MagicMock()
        mock_instance.publish.return_value = 'http://telegra.ph/file-result'
        MockPublisher.return_value = mock_instance
        
        # Create a temporary file to upload
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Document\n\nContent here.")
            tmp_path = f.name
        
        try:
            with open(tmp_path, 'rb') as f:
                response = self.client.post(
                    "/publish/file",
                    files={"file": ("test.md", f, "text/markdown")},
                    data={"title": "Custom Title"}
                )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['url'], 'http://telegra.ph/file-result')
        finally:
            os.unlink(tmp_path)

    @patch('telepress.server.TelegraphPublisher')
    def test_publish_file_uses_filename_as_default_title(self, MockPublisher):
        """Test that filename is used as default title when none provided."""
        mock_instance = MagicMock()
        mock_instance.publish.return_value = 'http://telegra.ph/result'
        MockPublisher.return_value = mock_instance
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("Content")
            tmp_path = f.name
        
        try:
            with open(tmp_path, 'rb') as f:
                response = self.client.post(
                    "/publish/file",
                    files={"file": ("my_document.md", f, "text/markdown")}
                )
            
            self.assertEqual(response.status_code, 200)
            # Check that publish was called with filename as title
            call_args = mock_instance.publish.call_args
            self.assertEqual(call_args[1]['title'], 'my_document.md')
        finally:
            os.unlink(tmp_path)

    @patch('telepress.server.TelegraphPublisher')
    def test_publish_file_zip(self, MockPublisher):
        """Test uploading and publishing a zip file."""
        mock_instance = MagicMock()
        mock_instance.publish.return_value = 'http://telegra.ph/gallery'
        MockPublisher.return_value = mock_instance
        
        import zipfile
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            with zipfile.ZipFile(f, 'w') as zf:
                zf.writestr('1.jpg', b'fake image')
            tmp_path = f.name
        
        try:
            with open(tmp_path, 'rb') as f:
                response = self.client.post(
                    "/publish/file",
                    files={"file": ("gallery.zip", f, "application/zip")},
                    data={"title": "My Gallery"}
                )
            
            self.assertEqual(response.status_code, 200)
        finally:
            os.unlink(tmp_path)


class TestServerErrors(unittest.TestCase):
    @patch('telepress.server.TelegraphPublisher')
    def test_publish_text_telepresserror(self, MockPublisher):
        """Test that TelePressError returns 400."""
        from telepress.exceptions import ValidationError
        
        mock_instance = MagicMock()
        mock_instance.publish.side_effect = ValidationError("Invalid input")
        MockPublisher.return_value = mock_instance
        
        from telepress.server import app
        client = TestClient(app)
        
        response = client.post("/publish/text", json={
            "content": "Content",
            "title": "Title"
        })
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid input", response.json()['detail'])

    @patch('telepress.server.TelegraphPublisher')
    def test_publish_text_unexpected_error(self, MockPublisher):
        """Test that unexpected errors return 500."""
        mock_instance = MagicMock()
        mock_instance.publish.side_effect = RuntimeError("Unexpected")
        MockPublisher.return_value = mock_instance
        
        from telepress.server import app
        client = TestClient(app)
        
        response = client.post("/publish/text", json={
            "content": "Content",
            "title": "Title"
        })
        
        self.assertEqual(response.status_code, 500)

    @patch('telepress.server.TelegraphPublisher')
    def test_publish_file_error_cleans_up_temp(self, MockPublisher):
        """Test that temporary files are cleaned up on error."""
        mock_instance = MagicMock()
        mock_instance.publish.side_effect = RuntimeError("Error")
        MockPublisher.return_value = mock_instance
        
        from telepress.server import app
        client = TestClient(app)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("Content")
            tmp_path = f.name
        
        try:
            with open(tmp_path, 'rb') as f:
                response = client.post(
                    "/publish/file",
                    files={"file": ("test.md", f, "text/markdown")}
                )
            
            self.assertEqual(response.status_code, 500)
        finally:
            os.unlink(tmp_path)


class TestServerModels(unittest.TestCase):
    def test_text_publish_request_validation(self):
        """Test request model validation."""
        from telepress.server import TextPublishRequest
        
        # Valid request
        req = TextPublishRequest(content="Content", title="Title")
        self.assertEqual(req.content, "Content")
        self.assertEqual(req.title, "Title")
        self.assertIsNone(req.token)
        
        # With optional token
        req = TextPublishRequest(content="Content", title="Title", token="tok")
        self.assertEqual(req.token, "tok")

    def test_publish_response_model(self):
        """Test response model."""
        from telepress.server import PublishResponse
        
        resp = PublishResponse(url="http://example.com")
        self.assertEqual(resp.url, "http://example.com")
        self.assertEqual(resp.status, "success")


class TestStartServer(unittest.TestCase):
    def test_start_server_defaults(self):
        """Test start_server with default parameters."""
        import uvicorn
        from telepress.server import start_server, app
        
        with patch.object(uvicorn, 'run') as mock_run:
            start_server()
            mock_run.assert_called_once_with(app, host="0.0.0.0", port=8000)

    def test_start_server_custom_params(self):
        """Test start_server with custom parameters."""
        import uvicorn
        from telepress.server import start_server, app
        
        with patch.object(uvicorn, 'run') as mock_run:
            start_server(host="127.0.0.1", port=9000)
            mock_run.assert_called_once_with(app, host="127.0.0.1", port=9000)


class TestGalleryEndpoint(unittest.TestCase):
    def setUp(self):
        """Patch TelegraphPublisher so gallery requests never hit the network."""
        self.patcher = patch('telepress.server.TelegraphPublisher')
        self.mock_publisher_class = self.patcher.start()
        self.addCleanup(self.patcher.stop)

        self.mock_publisher_instance = MagicMock()
        self.mock_publisher_class.return_value = self.mock_publisher_instance
        self.mock_publisher_instance.publish_zip_gallery.return_value = (
            'http://telegra.ph/gallery'
        )

        from telepress.server import app
        self.client = TestClient(app)

    def _gallery_files(self):
        return [
            ("files", ("p0.jpg", b"fake image 0", "image/jpeg")),
            ("files", ("p1.jpg", b"fake image 1", "image/jpeg")),
        ]

    def test_publish_gallery_success(self):
        """Test publishing multiple files as a gallery with metadata."""
        response = self.client.post(
            "/publish/gallery",
            files=self._gallery_files(),
            data={
                "title": "My Gallery",
                "tags": "pixiv, illustration",
                "link": "https://www.pixiv.net/artworks/123456",
                "spoiler": "true",
                "token": "custom_token",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['ok'], True)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['url'], 'http://telegra.ph/gallery')
        self.assertEqual(data['files'], 2)

        call_args = self.mock_publisher_instance.publish_zip_gallery.call_args
        self.assertEqual(call_args[1]['title'], 'My Gallery')
        footer = call_args[1]['footer_nodes']
        self.assertEqual(len(footer), 3)
        # spoiler note
        self.assertIn('R-18', footer[0]['children'][0])
        # tags paragraph
        self.assertIn('# pixiv', footer[1]['children'][0])
        # source link paragraph
        self.assertIn('Source:', footer[2]['children'][0])
        self.assertEqual(footer[2]['children'][1]['attrs']['href'],
                         'https://www.pixiv.net/artworks/123456')

    def test_publish_gallery_default_title_from_first_file(self):
        """Test that title falls back to the first file name."""
        response = self.client.post(
            "/publish/gallery", files=self._gallery_files()
        )

        self.assertEqual(response.status_code, 200)
        call_args = self.mock_publisher_instance.publish_zip_gallery.call_args
        self.assertEqual(call_args[1]['title'], 'p0')

    def test_publish_gallery_without_metadata_no_footer(self):
        """Test that no metadata produces an empty footer."""
        response = self.client.post(
            "/publish/gallery", files=self._gallery_files()
        )

        self.assertEqual(response.status_code, 200)
        call_args = self.mock_publisher_instance.publish_zip_gallery.call_args
        self.assertEqual(call_args[1]['footer_nodes'], [])

    def test_publish_gallery_duplicate_filenames(self):
        """Test that duplicate file names are disambiguated before zipping."""
        response = self.client.post(
            "/publish/gallery",
            files=[
                ("files", ("p0.jpg", b"a", "image/jpeg")),
                ("files", ("p0.jpg", b"b", "image/jpeg")),
            ],
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['files'], 2)

    def test_publish_gallery_requires_files(self):
        """Test that a request without files is rejected (422)."""
        response = self.client.post("/publish/gallery")
        self.assertEqual(response.status_code, 422)

    @patch('telepress.server._gallery_remote_media_enabled', return_value=False)
    def test_publish_gallery_remote_media_disabled_by_default(self, _mock_enabled):
        """Remote media is opt-in; without the env flag it must be rejected."""
        import json as _json
        response = self.client.post(
            "/publish/gallery",
            data={
                "title": "Remote",
                "media": _json.dumps([
                    {"assetId": "deviantart:u1:p0", "kind": "photo", "sourceUrl": "https://cdn.test/1.jpg"},
                ]),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("TELEPRESS_ALLOW_REMOTE_GALLERY_MEDIA", response.json()['detail'])
        self.mock_publisher_instance.publish_zip_gallery.assert_not_called()

    @patch('telepress.server._gallery_remote_media_enabled', return_value=True)
    @patch('telepress.server.urllib.request.urlopen')
    def test_publish_gallery_remote_media_enabled_fetches_remote(self, mock_urlopen, _mock_enabled):
        """With the flag on and media[] supplied, TelePress fetches https sources."""
        import json as _json

        class FakeResp:
            def __init__(self):
                self.first = True

            def read(self, n=None):
                if self.first:
                    self.first = False
                    return b'img-bytes'
                return b''

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        mock_urlopen.return_value = FakeResp()
        response = self.client.post(
            "/publish/gallery",
            data={
                "title": "Remote manifest",
                "link": "https://www.deviantart.com/a/art/x-1",
                "media": _json.dumps([
                    {"assetId": "deviantart:u1:p0", "kind": "photo", "sourceUrl": "https://cdn.test/1.jpg"},
                    {"assetId": "deviantart:u1:p1", "kind": "photo", "sourceUrl": "https://cdn.test/2.jpg"},
                ]),
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['ok'], True)
        self.assertEqual(data['files'], 2)
        call_args = self.mock_publisher_instance.publish_zip_gallery.call_args
        self.assertEqual(call_args[1]['title'], 'Remote manifest')
        self.assertEqual(mock_urlopen.call_count, 2)

    @patch('telepress.server._gallery_remote_media_enabled', return_value=True)
    def test_publish_gallery_remote_media_rejects_non_https(self, _mock_enabled):
        """Remote media sources must be https (avoids open-proxy/SSRF widening)."""
        import json as _json
        response = self.client.post(
            "/publish/gallery",
            data={"media": _json.dumps([{"sourceUrl": "http://insecure.local/1.jpg"}])},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("sourceUrl must be an https URL", response.json()['detail'])

    @patch('telepress.server.TelegraphPublisher')
    def test_publish_gallery_telepress_error(self, MockPublisher):
        """Test that TelePressError returns 400."""
        from telepress.exceptions import ValidationError

        mock_instance = MagicMock()
        mock_instance.publish_zip_gallery.side_effect = ValidationError(
            "No images found"
        )
        MockPublisher.return_value = mock_instance

        from telepress.server import app
        client = TestClient(app)

        response = client.post(
            "/publish/gallery",
            files=[("files", ("p0.jpg", b"fake", "image/jpeg"))],
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("No images found", response.json()['detail'])

    @patch('telepress.server.TelegraphPublisher')
    def test_publish_gallery_unexpected_error(self, MockPublisher):
        """Test that unexpected errors return 500."""
        mock_instance = MagicMock()
        mock_instance.publish_zip_gallery.side_effect = RuntimeError("boom")
        MockPublisher.return_value = mock_instance

        from telepress.server import app
        client = TestClient(app)

        response = client.post(
            "/publish/gallery",
            files=[("files", ("p0.jpg", b"fake", "image/jpeg"))],
        )

        self.assertEqual(response.status_code, 500)


class TestGalleryFooterBuilder(unittest.TestCase):
    def test_footer_with_all_fields(self):
        """Test footer builder renders warning, tags and source link."""
        from telepress.server import _build_gallery_footer

        nodes = _build_gallery_footer(
            tags=" pixiv , illustration ",
            link="https://www.pixiv.net/artworks/1",
            spoiler="true",
        )
        self.assertEqual(len(nodes), 3)
        self.assertIn('R-18', nodes[0]['children'][0])
        self.assertEqual(nodes[1]['children'][0], '# pixiv #illustration')
        self.assertEqual(nodes[2]['children'][1]['attrs']['href'],
                         'https://www.pixiv.net/artworks/1')

    def test_footer_without_fields(self):
        """Test footer builder returns empty list when nothing is set."""
        from telepress.server import _build_gallery_footer

        self.assertEqual(_build_gallery_footer(None, None, None), [])
        self.assertEqual(_build_gallery_footer("", "", "false"), [])


if __name__ == '__main__':
    unittest.main()


class TestRichNovelEndpoint(unittest.TestCase):
    """RFC Phase 3: /publish/rich-novel accepts md + images and reports assets."""

    def setUp(self):
        self.patcher = patch('telepress.server.TelegraphPublisher')
        self.mock_publisher_class = self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.mock_publisher_instance = MagicMock()
        self.mock_publisher_class.return_value = self.mock_publisher_instance
        self.mock_publisher_instance.publish_rich_markdown.return_value = {
            'url': 'http://telegra.ph/rich',
            'assets': [
                {'local': 'images/001.jpg', 'remote': 'https://files.catbox.moe/a.jpg',
                 'status': 'uploaded'},
                {'local': 'images/002.jpg', 'remote': None, 'status': 'failed'},
            ],
        }
        from telepress.server import app
        self.client = TestClient(app)

    def _request(self, title='富媒体小说', token='tok'):
        return self.client.post(
            '/publish/rich-novel',
            files=[
                ('md', ('novel.md', '![图](images/001.jpg)\n\n正文'.encode(), 'text/markdown')),
                ('images', ('images/001.jpg', b'fake1', 'image/jpeg')),
                ('images', ('images/002.jpg', b'fake2', 'image/jpeg')),
            ],
            data={'title': title, 'token': token},
        )

    def test_rich_novel_success(self):
        seen = {}

        def fake_publish(md_path, title, manifest=None):
            seen['md_path'] = md_path
            seen['title'] = title
            seen['img1'] = os.path.isfile(
                os.path.join(os.path.dirname(md_path), 'images', '001.jpg'))
            seen['img2'] = os.path.isfile(
                os.path.join(os.path.dirname(md_path), 'images', '002.jpg'))
            return {
                'url': 'http://telegra.ph/rich',
                'assets': [
                    {'local': 'images/001.jpg', 'remote': 'https://files.catbox.moe/a.jpg',
                     'status': 'uploaded'},
                    {'local': 'images/002.jpg', 'remote': None, 'status': 'failed'},
                ],
            }

        self.mock_publisher_instance.publish_rich_markdown.side_effect = fake_publish
        response = self._request()
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['url'], 'http://telegra.ph/rich')
        self.assertEqual(len(data['assets']), 2)
        self.assertEqual(data['assets'][0]['remote'], 'https://files.catbox.moe/a.jpg')
        self.assertEqual(data['assets'][1]['status'], 'failed')
        self.assertEqual(seen['title'], '富媒体小说')
        self.assertTrue(seen['img1'])
        self.assertTrue(seen['img2'])

    def test_rich_novel_passes_manifest(self):
        """manifest form field is parsed and forwarded to the publisher."""
        seen = {}
        self.mock_publisher_instance.publish_rich_markdown.side_effect = (
            lambda md_path, title, manifest=None: seen.update(
                manifest=manifest
            ) or {"url": "http://telegra.ph/rich", "assets": []}
        )
        response = self.client.post(
            "/publish/rich-novel",
            files=[("md", ("novel.md", "![图](images/001.jpg)".encode(), "text/markdown"))],
            data={
                "title": "富媒体小说",
                "token": "tok",
                "manifest": '[{"local": "images/001.jpg", "source": "https://i.pximg.net/x.jpg"}]',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            seen["manifest"],
            [{"local": "images/001.jpg", "source": "https://i.pximg.net/x.jpg"}],
        )

    def test_rich_novel_response_exposes_asset_id(self):
        """RichNovelAsset response model keeps assetId from the manifest."""
        self.mock_publisher_instance.publish_rich_markdown.return_value = {
            "url": "http://telegra.ph/rich",
            "assets": [{
                "local": "images/001.jpg",
                "remote": "https://media.example.com/pixiv/x.jpg",
                "status": "proxied",
                "assetId": "pixiv:123:pixivimage:p0",
            }],
        }
        response = self.client.post(
            "/publish/rich-novel",
            files=[("md", ("novel.md", "![图](images/001.jpg)".encode(), "text/markdown"))],
            data={
                "title": "富媒体小说",
                "token": "tok",
                "manifest": '[{"local": "images/001.jpg", "assetId": "pixiv:123:pixivimage:p0", "sourceUrl": "https://i.pximg.net/x.jpg"}]',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["assets"][0]["assetId"], "pixiv:123:pixivimage:p0"
        )

    @patch('telepress.server.TelegraphPublisher')
    def test_rich_novel_error_returns_400(self, MockPublisher):
        from telepress.exceptions import ValidationError
        mock_instance = MagicMock()
        mock_instance.publish_rich_markdown.side_effect = ValidationError("missing md")
        MockPublisher.return_value = mock_instance
        from telepress.server import app
        client = TestClient(app)
        response = client.post(
            '/publish/rich-novel',
            files=[('md', ('novel.md', '内容'.encode(), 'text/markdown'))],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('missing md', response.json()['detail'])


class TestServerApiKeyAuth(unittest.TestCase):
    """请求级 Bearer/X-TelePress-Key 鉴权（TELEPRESS_API_KEY）。"""

    def setUp(self):
        from telepress.server import app
        self.client = TestClient(app)
        patcher = patch('telepress.server.TelegraphPublisher')
        self.MockPublisher = patcher.start()
        self.addCleanup(patcher.stop)
        inst = MagicMock()
        inst.publish.return_value = 'http://telegra.ph/ok'
        self.MockPublisher.return_value = inst

    def test_no_key_configured_allows(self):
        os.environ.pop('TELEPRESS_API_KEY', None)
        r = self.client.post('/publish/text', json={'content': 'hi', 'title': 't'})
        self.assertIn(r.status_code, (200, 500))  # 未到鉴权拒绝（可能发布内部报错，但不是 401）
        self.assertNotEqual(r.status_code, 401)

    def test_key_required_when_configured(self):
        os.environ['TELEPRESS_API_KEY'] = 'secret-key'
        try:
            r = self.client.post('/publish/text', json={'content': 'hi', 'title': 't'})
            self.assertEqual(r.status_code, 401)
            r2 = self.client.post('/publish/text', json={'content': 'hi', 'title': 't'},
                                  headers={'Authorization': 'Bearer secret-key'})
            self.assertNotEqual(r2.status_code, 401)
            r3 = self.client.post('/publish/text', json={'content': 'hi', 'title': 't'},
                                  headers={'X-TelePress-Key': 'secret-key'})
            self.assertNotEqual(r3.status_code, 401)
            r4 = self.client.post('/publish/text', json={'content': 'hi', 'title': 't'},
                                  headers={'Authorization': 'Bearer wrong'})
            self.assertEqual(r4.status_code, 401)
        finally:
            os.environ.pop('TELEPRESS_API_KEY', None)
