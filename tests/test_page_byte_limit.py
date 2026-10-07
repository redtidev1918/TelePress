"""Rendered-byte pagination protects createPage and editPage, including Unicode."""
from unittest.mock import MagicMock, patch

import pytest
from telegraph.utils import json_dumps

from telepress.core import (
    TelegraphPublisher, TELEGRAPH_BODY_LIMIT, TELEGRAPH_CONTENT_LIMIT,
    _paginate_nodes, _split_markdown_chunks,
)
from telepress.exceptions import ValidationError


def byte_size(nodes):
    return len(json_dumps(nodes).encode("utf-8"))


def text_of(node):
    if isinstance(node, str):
        return node
    return "".join(text_of(child) for child in node.get("children", []))


@pytest.mark.parametrize("paragraph", ["测试段落。" * 10, "😀测试\\\"" * 10])
def test_publication_paginates_rendered_json_and_preserves_text(tmp_path, paragraph):
    # Less than 20k source characters can still exceed 64 KiB after rendering.
    content = (paragraph + "\n") * 390
    path = tmp_path / "novel.txt"
    path.write_text(content, encoding="utf-8")
    client = MagicMock()
    created = []
    edited = []

    def create_page(**kwargs):
        nodes = kwargs["content"]
        assert byte_size(nodes) <= TELEGRAPH_BODY_LIMIT
        created.append(nodes)
        return {"url": f"https://telegra.ph/part-{len(created)}", "path": f"part-{len(created)}"}

    def edit_page(**kwargs):
        assert byte_size(kwargs["content"]) <= TELEGRAPH_CONTENT_LIMIT
        edited.append(kwargs["content"])

    client.create_page.side_effect = create_page
    client.edit_page.side_effect = edit_page
    with patch("telepress.core.TelegraphAuth") as auth, patch("telepress.core.time.sleep"):
        auth.return_value.get_client.return_value = client
        publisher = TelegraphPublisher(token="fake", skip_duplicate=False)
        expected = [n for chunk in _split_markdown_chunks(content)
                    for n in publisher.converter.convert(chunk)]
        assert publisher.publish_markdown(str(path), "Unicode") == "https://telegra.ph/part-1"

    assert len(created) > 1
    assert len(edited) == len(created)
    assert "".join(text_of(n) for page in created for n in page) == "".join(text_of(n) for n in expected)


def test_oversized_nested_paragraph_keeps_formatting_and_unicode():
    text = "测试😀\\\"" * 20_000
    original = {"tag": "p", "children": [{"tag": "strong", "children": [text]}]}
    pages = _paginate_nodes([original])
    assert len(pages) > 1
    assert all(byte_size(page) <= TELEGRAPH_BODY_LIMIT for page in pages)
    assert "".join(text_of(n) for page in pages for n in page) == text
    assert all(n["tag"] == "p" and n["children"][0]["tag"] == "strong" for page in pages for n in page)


def test_oversized_indivisible_media_rejected_without_truncation():
    with pytest.raises(ValidationError, match="cannot fit"):
        _paginate_nodes([{"tag": "img", "attrs": {"src": "https://example.com/" + "a" * 70_000}}])


def test_provider_size_rejection_is_not_retried(tmp_path):
    path = tmp_path / "novel.txt"
    path.write_text("Test paragraph", encoding="utf-8")
    client = MagicMock()
    client.create_page.side_effect = RuntimeError("CONTENT_TOO_BIG")
    with patch("telepress.core.TelegraphAuth") as auth, patch("telepress.core.time.sleep") as sleep:
        auth.return_value.get_client.return_value = client
        publisher = TelegraphPublisher(token="fake", skip_duplicate=False)
        with pytest.raises(ValidationError, match="CONTENT_TOO_BIG"):
            publisher.publish_markdown(str(path), "Test")
    client.create_page.assert_called_once()
    sleep.assert_not_called()


def test_long_navigation_index_falls_back_to_compact_index():
    client = MagicMock()
    content = [{"tag": "p", "children": ["a" * 61_000]}]
    pages = [{"path": str(i), "url": "https://telegra.ph/" + "a" * 500 + str(i),
              "title": "Test", "content": content, "part_num": i + 1} for i in range(40)]
    with patch("telepress.core.TelegraphAuth") as auth:
        auth.return_value.get_client.return_value = client
        publisher = TelegraphPublisher(token="fake", skip_duplicate=False)
        publisher._link_pages(pages)
    assert client.edit_page.call_count == len(pages)
    for call in client.edit_page.call_args_list:
        nodes = call.kwargs["content"]
        assert byte_size(nodes) <= TELEGRAPH_CONTENT_LIMIT
        assert nodes[-1]["children"][0].startswith("Pages: ")
