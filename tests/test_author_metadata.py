import unittest
from unittest.mock import MagicMock, patch

from telepress import AuthorMetadata, publish, publish_text
from telepress.core import TelegraphPublisher
from telepress.exceptions import ValidationError


class TestAuthorMetadata(unittest.TestCase):
    def setUp(self):
        with patch('telepress.core.TelegraphAuth') as MockAuth:
            self.mock_client = MagicMock()
            self.mock_client.create_page.return_value = {
                'url': 'http://telegra.ph/page',
                'path': 'page',
            }
            MockAuth.return_value.get_client.return_value = self.mock_client
            self.publisher = TelegraphPublisher(token='fake', skip_duplicate=False)

    def test_default_publish_omits_author_fields(self):
        self.publisher.publish_text('content', title='Test')

        kwargs = self.mock_client.create_page.call_args.kwargs
        self.assertNotIn('author_name', kwargs)
        self.assertNotIn('author_url', kwargs)

    def test_publish_sends_both_author_fields(self):
        self.publisher.publish_text(
            'content',
            title='Test',
            author_name='Alice',
            author_url='https://example.com/alice',
        )

        kwargs = self.mock_client.create_page.call_args.kwargs
        self.assertEqual(kwargs['author_name'], 'Alice')
        self.assertEqual(kwargs['author_url'], 'https://example.com/alice')

    def test_publish_allows_author_name_without_url(self):
        self.publisher.publish_text('content', title='Test', author_name='Alice')

        kwargs = self.mock_client.create_page.call_args.kwargs
        self.assertEqual(kwargs['author_name'], 'Alice')
        self.assertNotIn('author_url', kwargs)

    def test_publish_allows_author_url_without_name(self):
        self.publisher.publish_text(
            'content', title='Test', author_url='https://example.com/alice'
        )

        kwargs = self.mock_client.create_page.call_args.kwargs
        self.assertEqual(kwargs['author_url'], 'https://example.com/alice')
        self.assertNotIn('author_name', kwargs)

    def test_paginated_publish_keeps_metadata_on_create_and_edit(self):
        image_urls = [f'https://example.com/{i}.jpg' for i in range(101)]
        self.mock_client.create_page.side_effect = [
            {'url': 'http://telegra.ph/page1', 'path': 'page1'},
            {'url': 'http://telegra.ph/page2', 'path': 'page2'},
        ]
        self.mock_client.edit_page.return_value = {}

        self.publisher.publish_optimized_gallery(
            image_urls,
            title='Gallery',
            author_name='Alice',
            author_url='https://example.com/alice',
        )

        for call in self.mock_client.create_page.call_args_list:
            self.assertEqual(call.kwargs['author_name'], 'Alice')
            self.assertEqual(call.kwargs['author_url'], 'https://example.com/alice')
        for call in self.mock_client.edit_page.call_args_list:
            self.assertEqual(call.kwargs['author_name'], 'Alice')
            self.assertEqual(call.kwargs['author_url'], 'https://example.com/alice')

    def test_invalid_author_name_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.publisher.publish_text('content', title='Test', author_name=123)

        self.mock_client.create_page.assert_not_called()

    def test_invalid_author_url_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.publisher.publish_text('content', title='Test', author_url='not-a-url')

        self.mock_client.create_page.assert_not_called()

    @patch('telepress.core._save_cache')
    @patch('telepress.core._load_cache', return_value={})
    def test_author_metadata_participates_in_deduplication(self, _load_cache, _save_cache):
        with patch('telepress.core.TelegraphAuth') as MockAuth:
            client = MagicMock()
            client.create_page.side_effect = [
                {'url': 'http://telegra.ph/alice', 'path': 'alice'},
                {'url': 'http://telegra.ph/bob', 'path': 'bob'},
            ]
            MockAuth.return_value.get_client.return_value = client
            publisher = TelegraphPublisher(token='fake', skip_duplicate=True)

        publisher.publish_text(
            'same content',
            title='Test',
            author_name='Alice',
            author_url='https://example.com/alice',
        )
        publisher.publish_text(
            'same content',
            title='Test',
            author_name='Bob',
            author_url='https://example.com/bob',
        )
        publisher.publish_text(
            'same content',
            title='Test',
            author_name='Alice',
            author_url='https://example.com/alice',
        )

        self.assertEqual(client.create_page.call_count, 2)

    @patch('telepress._get_publisher')
    def test_convenience_publish_forwards_author_metadata(self, mock_get_publisher):
        publisher = MagicMock()
        publisher.publish.return_value = 'http://telegra.ph/page'
        mock_get_publisher.return_value = publisher

        publish(
            'article.md',
            title='Test',
            author_name='Alice',
            author_url='https://example.com/alice',
        )

        publisher.publish.assert_called_once_with(
            'article.md',
            title='Test',
            author_name='Alice',
            author_url='https://example.com/alice',
            author=None,
        )

    @patch('telepress._get_publisher')
    def test_convenience_publish_text_forwards_author_metadata(self, mock_get_publisher):
        publisher = MagicMock()
        publisher.publish_text.return_value = 'http://telegra.ph/page'
        mock_get_publisher.return_value = publisher

        publish_text(
            'content',
            title='Test',
            author_name='Alice',
            author_url='https://example.com/alice',
        )

        publisher.publish_text.assert_called_once_with(
            'content',
            title='Test',
            author_name='Alice',
            author_url='https://example.com/alice',
            author=None,
        )


class TestAuthorMetadataObject(unittest.TestCase):
    """Structured AuthorMetadata call form (issue #72)."""

    def setUp(self):
        with patch('telepress.core.TelegraphAuth') as MockAuth:
            self.mock_client = MagicMock()
            self.mock_client.create_page.return_value = {
                'url': 'http://telegra.ph/page',
                'path': 'page',
            }
            MockAuth.return_value.get_client.return_value = self.mock_client
            self.publisher = TelegraphPublisher(token='fake', skip_duplicate=False)

    def test_object_publish_sends_both_author_fields(self):
        self.publisher.publish_text(
            'content',
            title='Test',
            author=AuthorMetadata(name='Alice', url='https://example.com/alice'),
        )

        kwargs = self.mock_client.create_page.call_args.kwargs
        self.assertEqual(kwargs['author_name'], 'Alice')
        self.assertEqual(kwargs['author_url'], 'https://example.com/alice')

    def test_object_allows_partial_fields(self):
        self.publisher.publish_text(
            'content', title='Test', author=AuthorMetadata(name='Alice')
        )
        kwargs = self.mock_client.create_page.call_args.kwargs
        self.assertEqual(kwargs['author_name'], 'Alice')
        self.assertNotIn('author_url', kwargs)

        self.publisher.publish_text(
            'content',
            title='Test',
            author=AuthorMetadata(url='https://example.com/alice'),
        )
        kwargs = self.mock_client.create_page.call_args.kwargs
        self.assertEqual(kwargs['author_url'], 'https://example.com/alice')
        self.assertNotIn('author_name', kwargs)

    def test_empty_object_omits_author_fields(self):
        self.publisher.publish_text('content', title='Test', author=AuthorMetadata())

        kwargs = self.mock_client.create_page.call_args.kwargs
        self.assertNotIn('author_name', kwargs)
        self.assertNotIn('author_url', kwargs)

    def test_mixing_object_and_flat_kwargs_raises(self):
        author = AuthorMetadata(name='Bob')

        with self.assertRaises(ValidationError):
            self.publisher.publish_text(
                'content', title='Test', author_name='Alice', author=author
            )
        with self.assertRaises(ValidationError):
            self.publisher.publish_text(
                'content',
                title='Test',
                author_url='https://example.com/alice',
                author=author,
            )

        self.mock_client.create_page.assert_not_called()

    def test_object_keeps_metadata_on_paginated_create_and_edit(self):
        image_urls = [f'https://example.com/{i}.jpg' for i in range(101)]
        self.mock_client.create_page.side_effect = [
            {'url': 'http://telegra.ph/page1', 'path': 'page1'},
            {'url': 'http://telegra.ph/page2', 'path': 'page2'},
        ]
        self.mock_client.edit_page.return_value = {}

        self.publisher.publish_optimized_gallery(
            image_urls,
            title='Gallery',
            author=AuthorMetadata(name='Alice', url='https://example.com/alice'),
        )

        for call in self.mock_client.create_page.call_args_list:
            self.assertEqual(call.kwargs['author_name'], 'Alice')
            self.assertEqual(call.kwargs['author_url'], 'https://example.com/alice')
        for call in self.mock_client.edit_page.call_args_list:
            self.assertEqual(call.kwargs['author_name'], 'Alice')
            self.assertEqual(call.kwargs['author_url'], 'https://example.com/alice')

    def test_object_reaches_telegraph_flat_fields(self):
        """The structured object must flatten to Telegraph's flat fields."""
        author = AuthorMetadata(name='Alice', url='https://example.com/alice')
        self.assertEqual(
            author.to_kwargs(),
            {'author_name': 'Alice', 'author_url': 'https://example.com/alice'},
        )
        self.assertEqual(AuthorMetadata().to_kwargs(), {})
        self.assertEqual(AuthorMetadata(name='Alice').to_kwargs(), {'author_name': 'Alice'})

    @patch('telepress.core._save_cache')
    @patch('telepress.core._load_cache', return_value={})
    def test_dedup_cache_key_matches_legacy_flat_form(self, _load_cache, _save_cache):
        """Object form and equivalent flat form must share one cache key."""
        with patch('telepress.core.TelegraphAuth') as MockAuth:
            client = MagicMock()
            client.create_page.return_value = {
                'url': 'http://telegra.ph/alice',
                'path': 'alice',
            }
            MockAuth.return_value.get_client.return_value = client
            publisher = TelegraphPublisher(token='fake', skip_duplicate=True)

        publisher.publish_text(
            'same content',
            title='Test',
            author_name='Alice',
            author_url='https://example.com/alice',
        )
        publisher.publish_text(
            'same content',
            title='Test',
            author=AuthorMetadata(name='Alice', url='https://example.com/alice'),
        )

        self.assertEqual(client.create_page.call_count, 1)


class TestAuthorMetadataValidation(unittest.TestCase):
    """AuthorMetadata validates itself on construction."""

    def test_non_string_name_raises(self):
        with self.assertRaises(ValidationError):
            AuthorMetadata(name=123)

    def test_non_string_url_raises(self):
        with self.assertRaises(ValidationError):
            AuthorMetadata(url=123)

    def test_url_with_whitespace_raises(self):
        with self.assertRaises(ValidationError):
            AuthorMetadata(url='https://example.com/a b')

    def test_non_http_url_raises(self):
        with self.assertRaises(ValidationError):
            AuthorMetadata(url='not-a-url')
        with self.assertRaises(ValidationError):
            AuthorMetadata(url='ftp://example.com/alice')

    def test_both_fields_optional(self):
        author = AuthorMetadata()
        self.assertIsNone(author.name)
        self.assertIsNone(author.url)
        self.assertEqual(author.to_kwargs(), {})


class TestConvenienceAuthorObject(unittest.TestCase):
    @patch('telepress._get_publisher')
    def test_convenience_publish_forwards_author_object(self, mock_get_publisher):
        publisher = MagicMock()
        publisher.publish.return_value = 'http://telegra.ph/page'
        mock_get_publisher.return_value = publisher
        author = AuthorMetadata(name='Alice', url='https://example.com/alice')

        publish('article.md', title='Test', author=author)

        publisher.publish.assert_called_once_with(
            'article.md',
            title='Test',
            author_name=None,
            author_url=None,
            author=author,
        )

    @patch('telepress._get_publisher')
    def test_convenience_publish_text_forwards_author_object(self, mock_get_publisher):
        publisher = MagicMock()
        publisher.publish_text.return_value = 'http://telegra.ph/page'
        mock_get_publisher.return_value = publisher
        author = AuthorMetadata(name='Alice', url='https://example.com/alice')

        publish_text('content', title='Test', author=author)

        publisher.publish_text.assert_called_once_with(
            'content',
            title='Test',
            author_name=None,
            author_url=None,
            author=author,
        )


if __name__ == '__main__':
    unittest.main()
