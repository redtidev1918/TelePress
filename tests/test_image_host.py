"""
Tests for image_host module.
"""
import unittest
import os
import tempfile
import json
from unittest.mock import patch, MagicMock, Mock

from telepress.image_host import (
    ImageHost, ImgbbHost, ImgurHost, SmmsHost, CatboxHost, FreeImageHost, UploadcareHost,
    ImageKitHost, CloudinaryHost, ZeroXZeroHost, LitterboxHost, R2Host, S3Host, CustomHost,
    create_image_host, IMAGE_HOSTS, HOST_ALIASES
)
from telepress.exceptions import UploadError


class TestImgbbHost(unittest.TestCase):
    """Tests for ImgbbHost."""
    
    def test_init_requires_api_key(self):
        """Test that ImgbbHost requires an API key."""
        with self.assertRaises(ValueError) as ctx:
            ImgbbHost(api_key='')
        self.assertIn('API key', str(ctx.exception))
    
    def test_init_success(self):
        """Test successful initialization."""
        host = ImgbbHost(api_key='test_key')
        self.assertEqual(host.name, 'imgbb')
        self.assertEqual(host.api_key, 'test_key')
    
    @patch('telepress.image_host.requests.post')
    def test_upload_success(self, mock_post):
        """Test successful upload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'data': {'url': 'https://i.ibb.co/xxx/image.jpg'}
        }
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake image data')
            tmp_path = f.name
        
        try:
            host = ImgbbHost(api_key='test_key')
            url = host.upload(tmp_path)
            self.assertEqual(url, 'https://i.ibb.co/xxx/image.jpg')
        finally:
            os.unlink(tmp_path)
    
    @patch('telepress.image_host.requests.post')
    def test_upload_failure(self, mock_post):
        """Test upload failure handling."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = 'Bad request'
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake image data')
            tmp_path = f.name
        
        try:
            host = ImgbbHost(api_key='test_key')
            with self.assertRaises(UploadError):
                host.upload(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    def test_upload_file_not_found(self):
        """Test upload with non-existent file."""
        host = ImgbbHost(api_key='test_key')
        with self.assertRaises(FileNotFoundError):
            host.upload('/nonexistent/path.jpg')


class TestImgurHost(unittest.TestCase):
    """Tests for ImgurHost."""
    
    def test_init_requires_client_id(self):
        """Test that ImgurHost requires a client ID."""
        with self.assertRaises(ValueError) as ctx:
            ImgurHost(client_id='')
        self.assertIn('Client ID', str(ctx.exception))
    
    def test_init_success(self):
        """Test successful initialization."""
        host = ImgurHost(client_id='test_client_id')
        self.assertEqual(host.name, 'imgur')
        self.assertEqual(host.client_id, 'test_client_id')
    
    @patch('telepress.image_host.requests.post')
    def test_upload_success(self, mock_post):
        """Test successful upload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'data': {'link': 'https://i.imgur.com/xxx.jpg'}
        }
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake image data')
            tmp_path = f.name
        
        try:
            host = ImgurHost(client_id='test_client_id')
            url = host.upload(tmp_path)
            self.assertEqual(url, 'https://i.imgur.com/xxx.jpg')
        finally:
            os.unlink(tmp_path)


class TestSmmsHost(unittest.TestCase):
    """Tests for SmmsHost."""
    
    def test_init_requires_api_token(self):
        """Test that SmmsHost requires an API token."""
        with self.assertRaises(ValueError) as ctx:
            SmmsHost(api_token='')
        self.assertIn('API token', str(ctx.exception))
    
    def test_init_success(self):
        """Test successful initialization."""
        host = SmmsHost(api_token='test_token')
        self.assertEqual(host.name, 'smms')
        self.assertEqual(host.api_token, 'test_token')
    
    @patch('telepress.image_host.requests.post')
    def test_upload_success(self, mock_post):
        """Test successful upload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'data': {'url': 'https://i.loli.net/xxx.jpg'}
        }
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake image data')
            tmp_path = f.name
        
        try:
            host = SmmsHost(api_token='test_token')
            url = host.upload(tmp_path)
            self.assertEqual(url, 'https://i.loli.net/xxx.jpg')
        finally:
            os.unlink(tmp_path)
    
    @patch('telepress.image_host.requests.post')
    def test_upload_image_repeated(self, mock_post):
        """Test handling of repeated image upload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': False,
            'code': 'image_repeated',
            'images': 'https://existing.url/image.jpg'
        }
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake image data')
            tmp_path = f.name
        
        try:
            host = SmmsHost(api_token='test_token')
            url = host.upload(tmp_path)
            self.assertEqual(url, 'https://existing.url/image.jpg')
        finally:
            os.unlink(tmp_path)


class TestS3Host(unittest.TestCase):
    """Tests for S3Host."""
    
    def test_init_requires_credentials(self):
        """Test that S3Host requires necessary credentials."""
        with self.assertRaises(ValueError) as ctx:
            S3Host(access_key_id='', secret_access_key='', bucket='', public_url='')
        self.assertIn('S3 requires', str(ctx.exception))
    
    def test_init_success(self):
        """Test successful initialization."""
        host = S3Host(
            access_key_id='key123',
            secret_access_key='secret123',
            bucket='my-bucket',
            public_url='https://s3.example.com',
            endpoint_url='https://endpoint'
        )
        self.assertEqual(host.name, 's3')
        self.assertEqual(host.bucket, 'my-bucket')
        self.assertEqual(host.public_url, 'https://s3.example.com')
    
    def test_r2_alias(self):
        """Test R2Host alias."""
        host = R2Host(
            account_id='acc123',
            access_key_id='key123',
            secret_access_key='secret123',
            bucket='my-bucket',
            public_url='https://pub.r2.dev'
        )
        self.assertEqual(host.name, 'r2')
        self.assertEqual(host.endpoint_url, 'https://acc123.r2.cloudflarestorage.com')

    def test_public_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from public_url."""
        host = S3Host(
            access_key_id='key123',
            secret_access_key='secret123',
            bucket='my-bucket',
            public_url='https://s3.example.com/',
            endpoint_url='https://endpoint'
        )
        self.assertEqual(host.public_url, 'https://s3.example.com')
    
    def test_upload_success(self):
        """Test successful upload to S3 (requires boto3)."""
        try:
            import boto3
        except ImportError:
            self.skipTest("boto3 not installed")
        
        # Mock boto3.client
        with patch.object(boto3, 'client') as mock_boto_client:
            mock_client = MagicMock()
            mock_boto_client.return_value = mock_client
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                f.write(b'fake image data')
                tmp_path = f.name
            
            try:
                host = S3Host(
                    access_key_id='key123',
                    secret_access_key='secret123',
                    bucket='my-bucket',
                    public_url='https://s3.example.com',
                    endpoint_url='https://endpoint'
                )
                url = host.upload(tmp_path)
                
                self.assertTrue(url.startswith('https://s3.example.com/'))
                self.assertTrue(url.endswith('.jpg'))
                mock_client.upload_fileobj.assert_called_once()
            finally:
                os.unlink(tmp_path)


class TestCustomHost(unittest.TestCase):
    """Tests for CustomHost."""
    
    def test_init_requires_upload_url(self):
        """Test that CustomHost requires upload_url."""
        with self.assertRaises(ValueError) as ctx:
            CustomHost(upload_url='')
        self.assertIn('upload_url', str(ctx.exception))
    
    def test_init_success(self):
        """Test successful initialization."""
        host = CustomHost(
            upload_url='https://api.example.com/upload',
            headers={'Authorization': 'Bearer token'},
            response_url_path='data.url'
        )
        self.assertEqual(host.name, 'custom')
        self.assertEqual(host.upload_url, 'https://api.example.com/upload')
        self.assertEqual(host.response_url_path, 'data.url')
    
    def test_init_defaults(self):
        """Test default values."""
        host = CustomHost(upload_url='https://api.example.com/upload')
        self.assertEqual(host.method, 'POST')
        self.assertEqual(host.file_field, 'file')
        self.assertEqual(host.response_url_path, 'url')
        self.assertEqual(host.headers, {})
        self.assertEqual(host.extra_data, {})
    
    @patch('telepress.image_host.requests.post')
    def test_upload_success_simple_path(self, mock_post):
        """Test upload with simple response URL path."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'url': 'https://example.com/image.jpg'}
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake image data')
            tmp_path = f.name
        
        try:
            host = CustomHost(
                upload_url='https://api.example.com/upload',
                response_url_path='url'
            )
            url = host.upload(tmp_path)
            self.assertEqual(url, 'https://example.com/image.jpg')
        finally:
            os.unlink(tmp_path)
    
    @patch('telepress.image_host.requests.post')
    def test_upload_success_nested_path(self, mock_post):
        """Test upload with nested response URL path."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'data': {
                'url': 'https://example.com/nested/image.jpg'
            }
        }
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake image data')
            tmp_path = f.name
        
        try:
            host = CustomHost(
                upload_url='https://api.example.com/upload',
                response_url_path='data.url'
            )
            url = host.upload(tmp_path)
            self.assertEqual(url, 'https://example.com/nested/image.jpg')
        finally:
            os.unlink(tmp_path)
    
    @patch('telepress.image_host.requests.post')
    def test_upload_success_array_path(self, mock_post):
        """Test upload with array index in response URL path."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'files': [
                {'url': 'https://example.com/first.jpg'},
                {'url': 'https://example.com/second.jpg'}
            ]
        }
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake image data')
            tmp_path = f.name
        
        try:
            host = CustomHost(
                upload_url='https://api.example.com/upload',
                response_url_path='files.0.url'
            )
            url = host.upload(tmp_path)
            self.assertEqual(url, 'https://example.com/first.jpg')
        finally:
            os.unlink(tmp_path)
    
    @patch('telepress.image_host.requests.post')
    def test_upload_invalid_response_path(self, mock_post):
        """Test upload with invalid response path."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'other': 'data'}
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake image data')
            tmp_path = f.name
        
        try:
            host = CustomHost(
                upload_url='https://api.example.com/upload',
                response_url_path='data.url'
            )
            with self.assertRaises(UploadError):
                host.upload(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    @patch('telepress.image_host.requests.post')
    def test_upload_with_headers(self, mock_post):
        """Test that headers are sent with request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'url': 'https://example.com/image.jpg'}
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake image data')
            tmp_path = f.name
        
        try:
            host = CustomHost(
                upload_url='https://api.example.com/upload',
                headers={'Authorization': 'Bearer token123', 'X-Custom': 'value'}
            )
            host.upload(tmp_path)
            
            call_kwargs = mock_post.call_args[1]
            self.assertEqual(call_kwargs['headers']['Authorization'], 'Bearer token123')
            self.assertEqual(call_kwargs['headers']['X-Custom'], 'value')
        finally:
            os.unlink(tmp_path)


class TestCatboxHost(unittest.TestCase):
    """Tests for CatboxHost."""

    def test_init_anonymous(self):
        """Test anonymous initialization."""
        host = CatboxHost()
        self.assertEqual(host.name, 'catbox')
        self.assertIsNone(host.userhash)

    def test_init_with_userhash(self):
        """Test initialization with userhash."""
        host = CatboxHost(userhash='my-hash')
        self.assertEqual(host.userhash, 'my-hash')

    @patch('telepress.image_host.requests.post')
    def test_upload_success_anonymous(self, mock_post):
        """Test anonymous upload success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'https://files.catbox.moe/abcdef.png'
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'fake file data')
            tmp_path = f.name

        try:
            host = CatboxHost()
            url = host.upload(tmp_path)
            self.assertEqual(url, 'https://files.catbox.moe/abcdef.png')
            call_kwargs = mock_post.call_args[1]
            self.assertEqual(call_kwargs['data']['reqtype'], 'fileupload')
            self.assertNotIn('userhash', call_kwargs['data'])
            self.assertIn('fileToUpload', call_kwargs['files'])
        finally:
            os.unlink(tmp_path)

    @patch('telepress.image_host.requests.post')
    def test_upload_success_with_userhash(self, mock_post):
        """Test upload includes userhash when configured."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'https://files.catbox.moe/abc123.txt'
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'plain text')
            tmp_path = f.name

        try:
            host = CatboxHost(userhash='test-userhash')
            url = host.upload(tmp_path)
            self.assertEqual(url, 'https://files.catbox.moe/abc123.txt')
            call_kwargs = mock_post.call_args[1]
            self.assertEqual(call_kwargs['data']['reqtype'], 'fileupload')
            self.assertEqual(call_kwargs['data']['userhash'], 'test-userhash')
            self.assertIn('fileToUpload', call_kwargs['files'])
        finally:
            os.unlink(tmp_path)

    @patch('telepress.image_host.requests.post')
    def test_upload_non_200_raises(self, mock_post):
        """Test non-200 response raises UploadError without leaking userhash."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'File too large.'
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'fake data')
            tmp_path = f.name

        try:
            host = CatboxHost(userhash='secret-hash')
            with self.assertRaises(UploadError) as ctx:
                host.upload(tmp_path)
            self.assertNotIn('secret-hash', str(ctx.exception))
        finally:
            os.unlink(tmp_path)

    @patch('telepress.image_host.requests.post')
    def test_upload_invalid_response_raises(self, mock_post):
        """Test 200 with non-URL response raises UploadError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'File too large.'
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'fake data')
            tmp_path = f.name

        try:
            host = CatboxHost()
            with self.assertRaises(UploadError):
                host.upload(tmp_path)
        finally:
            os.unlink(tmp_path)

    @patch('telepress.image_host.requests.post')
    def test_upload_empty_response_raises(self, mock_post):
        """Test empty 200 response raises UploadError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = ''
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'fake data')
            tmp_path = f.name

        try:
            host = CatboxHost()
            with self.assertRaises(UploadError):
                host.upload(tmp_path)
        finally:
            os.unlink(tmp_path)

    @patch('telepress.image_host.requests.post')
    def test_upload_accepts_plain_files(self, mock_post):
        """Test upload does not reject non-image files."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'https://files.catbox.moe/archive.zip'
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            f.write(b'zip contents')
            tmp_path = f.name

        try:
            host = CatboxHost()
            url = host.upload(tmp_path)
            self.assertEqual(url, 'https://files.catbox.moe/archive.zip')
        finally:
            os.unlink(tmp_path)

    def test_upload_file_not_found(self):
        """Test upload with non-existent file."""
        host = CatboxHost()
        with self.assertRaises(FileNotFoundError):
            host.upload('/nonexistent/path.dat')


class TestFreeImageHost(unittest.TestCase):
    """Tests for FreeImageHost."""

    def test_requires_api_key(self):
        with self.assertRaises(ValueError):
            FreeImageHost(api_key='')

    @patch('telepress.image_host.requests.post')
    def test_upload_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status_txt': 'OK', 'data': {'image': {'url': 'https://freeimage.host/x.png'}}}
        mock_post.return_value = mock_response
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'data')
            tmp = f.name
        try:
            host = FreeImageHost(api_key='k')
            self.assertEqual(host.upload(tmp), 'https://freeimage.host/x.png')
            self.assertEqual(mock_post.call_args[1]['data']['format'], 'json')
            self.assertIn('source', mock_post.call_args[1]['files'])
        finally:
            os.unlink(tmp)

    @patch('telepress.image_host.requests.post')
    def test_upload_failure(self, mock_post):
        mock_response = MagicMock(); mock_response.status_code = 500; mock_response.text = 'bad'
        mock_post.return_value = mock_response
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            tmp = f.name
        try:
            with self.assertRaises(UploadError):
                FreeImageHost(api_key='k').upload(tmp)
        finally:
            os.unlink(tmp)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            FreeImageHost(api_key='k').upload('/no/such.png')


class TestUploadcareHost(unittest.TestCase):
    """Tests for UploadcareHost."""

    def test_requires_public_key(self):
        with self.assertRaises(ValueError):
            UploadcareHost(public_key='')

    @patch('telepress.image_host.requests.post')
    def test_upload_returns_cdn_url(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'file': 'abc-123'}
        mock_post.return_value = mock_response
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'x')
            tmp = f.name
        try:
            host = UploadcareHost(public_key='pub')
            self.assertEqual(host.upload(tmp), 'https://ucarecdn.com/abc-123')
            data = mock_post.call_args[1]['data']
            self.assertEqual(data['UPLOADCARE_PUB_KEY'], 'pub')
            self.assertIn('file', mock_post.call_args[1]['files'])
        finally:
            os.unlink(tmp)

    @patch('telepress.image_host.requests.post')
    def test_upload_missing_uuid(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            tmp = f.name
        try:
            with self.assertRaises(UploadError):
                UploadcareHost(public_key='pub').upload(tmp)
        finally:
            os.unlink(tmp)


class TestImageKitHost(unittest.TestCase):
    """Tests for ImageKitHost."""

    def test_requires_private_key(self):
        with self.assertRaises(ValueError):
            ImageKitHost(private_key='')

    @patch('telepress.image_host.requests.post')
    def test_upload_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'url': 'https://ik.imagekit.io/x/file.png'}
        mock_post.return_value = mock_response
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'x')
            tmp = f.name
        try:
            host = ImageKitHost(private_key='pk')
            self.assertEqual(host.upload(tmp), 'https://ik.imagekit.io/x/file.png')
            kwargs = mock_post.call_args[1]
            auth = kwargs['headers']['Authorization']
            self.assertTrue(auth.startswith('Basic '))
            import base64 as _b64
            self.assertEqual(
                _b64.b64decode(auth.split(' ', 1)[1]).decode(), 'pk:'
            )
            self.assertEqual(kwargs['data']['fileName'], os.path.basename(tmp))
            self.assertIn('file', kwargs['files'])
        finally:
            os.unlink(tmp)


class TestCloudinaryHost(unittest.TestCase):
    """Tests for CloudinaryHost."""

    def test_requires_preset_or_keys(self):
        with self.assertRaises(ValueError):
            CloudinaryHost(cloud_name='cloud')

    @patch('telepress.image_host.requests.post')
    def test_unsigned_upload_preset(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'secure_url': 'https://res.cloudinary.com/c/image/upload/v1/x.png'}
        mock_post.return_value = mock_response
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'x')
            tmp = f.name
        try:
            host = CloudinaryHost(cloud_name='c', upload_preset='p')
            self.assertEqual(host.upload(tmp), 'https://res.cloudinary.com/c/image/upload/v1/x.png')
            self.assertEqual(mock_post.call_args[1]['data']['upload_preset'], 'p')
        finally:
            os.unlink(tmp)

    @patch('telepress.image_host.requests.post')
    def test_signed_upload(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'secure_url': 'https://res.cloudinary.com/c/image/upload/v1/s.png'}
        mock_post.return_value = mock_response
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'x')
            tmp = f.name
        try:
            host = CloudinaryHost(cloud_name='c', api_key='key', api_secret='secret')
            url = host.upload(tmp)
            self.assertTrue(url.startswith('https://'))
            data = mock_post.call_args[1]['data']
            self.assertIn('signature', data)
            self.assertNotIn('secret', str(data))
        finally:
            os.unlink(tmp)


class TestZeroXZeroHost(unittest.TestCase):
    """Tests for ZeroXZeroHost (0x0.st)."""

    @patch('telepress.image_host.requests.post')
    def test_upload(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'https://0x0.st/abc.txt'
        mock_post.return_value = mock_response
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'x')
            tmp = f.name
        try:
            self.assertEqual(ZeroXZeroHost().upload(tmp), 'https://0x0.st/abc.txt')
        finally:
            os.unlink(tmp)

    @patch('telepress.image_host.requests.post')
    def test_invalid_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'error'
        mock_post.return_value = mock_response
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            tmp = f.name
        try:
            with self.assertRaises(UploadError):
                ZeroXZeroHost().upload(tmp)
        finally:
            os.unlink(tmp)


class TestLitterboxHost(unittest.TestCase):
    """Tests for LitterboxHost."""

    def test_invalid_expiration(self):
        with self.assertRaises(ValueError):
            LitterboxHost(expiration='99h')

    @patch('telepress.image_host.requests.post')
    def test_upload(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'https://files.litterbox.catbox.moe/abc.png'
        mock_post.return_value = mock_response
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'x')
            tmp = f.name
        try:
            host = LitterboxHost(expiration='24h')
            self.assertEqual(host.upload(tmp), 'https://files.litterbox.catbox.moe/abc.png')
            self.assertEqual(mock_post.call_args[1]['data']['time'], '24h')
        finally:
            os.unlink(tmp)



class TestCreateImageHost(unittest.TestCase):
    """Tests for create_image_host function."""
    
    def test_create_imgbb(self):
        """Test creating imgbb host."""
        host = create_image_host('imgbb', api_key='test_key')
        self.assertIsInstance(host, ImgbbHost)
    
    def test_create_imgur(self):
        """Test creating imgur host."""
        host = create_image_host('imgur', client_id='test_id')
        self.assertIsInstance(host, ImgurHost)
    
    def test_create_smms(self):
        """Test creating smms host."""
        host = create_image_host('smms', api_token='test_token')
        self.assertIsInstance(host, SmmsHost)

    def test_create_catbox_anonymous(self):
        """Test creating anonymous catbox host."""
        host = create_image_host('catbox')
        self.assertIsInstance(host, CatboxHost)
        self.assertIsNone(host.userhash)

    def test_create_catbox_with_userhash(self):
        """Test creating catbox host with userhash."""
        host = create_image_host('catbox', userhash='my-hash')
        self.assertIsInstance(host, CatboxHost)
        self.assertEqual(host.userhash, 'my-hash')

    def test_create_new_hosts(self):
        self.assertIsInstance(create_image_host('freeimage', api_key='k'), FreeImageHost)
        self.assertIsInstance(create_image_host('uploadcare', public_key='p'), UploadcareHost)
        self.assertIsInstance(create_image_host('imagekit', private_key='k'), ImageKitHost)
        self.assertIsInstance(create_image_host('cloudinary', cloud_name='c', upload_preset='p'), CloudinaryHost)
        self.assertIsInstance(create_image_host('0x0'), ZeroXZeroHost)
        self.assertIsInstance(create_image_host('litterbox', expiration='1h'), LitterboxHost)

    def test_host_aliases(self):
        self.assertEqual(HOST_ALIASES['freeimagehost'], 'freeimage')
        self.assertEqual(HOST_ALIASES['zeroxzero'], '0x0')
        self.assertIsInstance(create_image_host('freeimagehost', api_key='k'), FreeImageHost)
        self.assertIsInstance(create_image_host('zeroxzero'), ZeroXZeroHost)

    def test_create_s3(self):
        """Test creating s3 host."""
        host = create_image_host('s3',
            access_key_id='key',
            secret_access_key='secret',
            bucket='bucket',
            public_url='https://s3.example.com',
            endpoint_url='https://endpoint'
        )
        self.assertIsInstance(host, S3Host)
        self.assertEqual(host.name, 's3')

    def test_create_r2(self):
        """Test creating r2 host."""
        host = create_image_host('r2',
            account_id='acc123',
            access_key_id='key',
            secret_access_key='secret',
            bucket='bucket',
            public_url='https://example.com'
        )
        self.assertIsInstance(host, R2Host)
        self.assertEqual(host.name, 'r2')
    
    def test_create_custom(self):
        """Test creating custom host."""
        host = create_image_host('custom', upload_url='https://api.example.com/upload')
        self.assertIsInstance(host, CustomHost)
    
    def test_create_unknown_host(self):
        """Test creating unknown host raises error."""
        with self.assertRaises(ValueError) as ctx:
            create_image_host('unknown_host')
        self.assertIn('Unknown image host', str(ctx.exception))
        self.assertIn('Available:', str(ctx.exception))
    
    @patch('telepress.config.load_config')
    def test_create_from_config(self, mock_load_config):
        """Test creating host from config when no name specified."""
        mock_load_config.return_value = {
            'image_host': {
                'type': 'imgbb',
                'api_key': 'config_key'
            }
        }
        
        host = create_image_host()
        self.assertIsInstance(host, ImgbbHost)
        self.assertEqual(host.api_key, 'config_key')
    
    @patch('telepress.config.load_config')
    def test_create_from_empty_config_raises(self, mock_load_config):
        """Test that empty config raises error."""
        mock_load_config.return_value = {}
        
        with self.assertRaises(ValueError) as ctx:
            create_image_host()
        self.assertIn('No image host configured', str(ctx.exception))
    
    @patch('telepress.config.load_config')
    def test_create_config_missing_type_raises(self, mock_load_config):
        """Test that config without type raises error."""
        mock_load_config.return_value = {'image_host': {'api_key': 'some_key'}}
        
        with self.assertRaises(ValueError) as ctx:
            create_image_host()
        self.assertIn("missing 'type'", str(ctx.exception))


class TestImageHostsRegistry(unittest.TestCase):
    """Tests for IMAGE_HOSTS registry."""
    
    def test_all_hosts_registered(self):
        """Test that all expected hosts are registered."""
        expected = {'imgbb', 'imgur', 'smms', 'catbox', 'freeimage', 'uploadcare', 'imagekit', 'cloudinary', '0x0', 'litterbox', 'r2', 's3', 'custom', 'rclone'}
        self.assertEqual(set(IMAGE_HOSTS.keys()), expected)
    
    def test_all_hosts_are_image_host_subclass(self):
        """Test that all registered hosts inherit from ImageHost."""
        for name, host_class in IMAGE_HOSTS.items():
            self.assertTrue(
                issubclass(host_class, ImageHost),
                f"{name} should be a subclass of ImageHost"
            )


if __name__ == '__main__':
    unittest.main()
