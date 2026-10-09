"""Rendered-byte pagination protects createPage and editPage, including Unicode."""
from unittest.mock import MagicMock, patch

import pytest
from telegraph.utils import json_dumps

from telepress.core import (
    TelegraphPublisher, TELEGRAPH_BODY_LIMIT, TELEGRAPH_CONTENT_LIMIT,
    MARKDOWN_PAGE_CHUNK_SIZE, _paginate_nodes,
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
        expected = publisher.converter.convert(content)
        assert publisher.publish_markdown(str(path), "Unicode") == "https://telegra.ph/part-1"

    assert len(created) > 1
    assert len(edited) == len(created)
    assert "".join(text_of(n) for page in created for n in page) == "".join(text_of(n) for n in expected)


def test_cjk_publication_does_not_strand_short_pages_between_source_chunks(tmp_path):
    paragraphs = [f"段落{i:04d}：" + "测试正文。" * 18 for i in range(900)]
    path = tmp_path / "novel.txt"
    path.write_text("\n".join(paragraphs), encoding="utf-8")
    client = MagicMock()
    client.create_page.side_effect = lambda **kw: {
        "url": f"https://telegra.ph/part-{client.create_page.call_count}",
        "path": f"part-{client.create_page.call_count}",
    }
    with patch("telepress.core.TelegraphAuth") as auth, patch("telepress.core.time.sleep"):
        auth.return_value.get_client.return_value = client
        publisher = TelegraphPublisher(token="fake", skip_duplicate=False)
        publisher.publish_markdown(str(path), "Pagination regression")
    pages = [call.kwargs["content"] for call in client.create_page.call_args_list]
    assert len(pages) == 5
    assert all(TELEGRAPH_BODY_LIMIT * 0.95 < byte_size(page) <= TELEGRAPH_BODY_LIMIT
               for page in pages[:-1])
    # Compare to the source itself, not another invocation of the paginator.
    assert "".join(text_of(n) for page in pages for n in page) == "".join(paragraphs)
    assert client.edit_page.call_count == len(pages)
    for call in client.edit_page.call_args_list:
        assert byte_size(call.kwargs["content"]) <= TELEGRAPH_CONTENT_LIMIT


def test_markdown_spanning_old_source_boundary_retains_formatting(tmp_path):
    body = "边界测试" * 12_000
    path = tmp_path / "formatted.md"
    path.write_text("**" + body + "**", encoding="utf-8")
    client = MagicMock()
    client.create_page.return_value = {"url": "https://telegra.ph/test", "path": "test"}
    with patch("telepress.core.TelegraphAuth") as auth, patch("telepress.core.time.sleep"):
        auth.return_value.get_client.return_value = client
        publisher = TelegraphPublisher(token="fake", skip_duplicate=False)
        publisher.publish_markdown(str(path), "Formatting regression")
    pages = [call.kwargs["content"] for call in client.create_page.call_args_list]
    assert "".join(text_of(n) for page in pages for n in page) == body
    assert all(n["children"][0]["tag"] == "strong" for page in pages for n in page)
    assert all(sum(len(text_of(n)) for n in page) <= MARKDOWN_PAGE_CHUNK_SIZE for page in pages)
    assert all(byte_size(page) <= TELEGRAPH_BODY_LIMIT for page in pages)


def test_text_endpoint_preserves_cross_boundary_reference_links(tmp_path):
    from fastapi.testclient import TestClient
    from telepress.server import app

    content = "[Reference][target]\n\n" + ("测试正文。" * 20 + "\n\n") * 500
    content += "\n[target]: https://example.com/reference\n"
    client = MagicMock()
    client.create_page.side_effect = lambda **kw: {
        "url": f"https://telegra.ph/part-{client.create_page.call_count}",
        "path": f"part-{client.create_page.call_count}",
    }
    # The endpoint builds its own publisher with skip_duplicate enabled, which
    # reads the persistent ~/.telepress_cache.json dedup cache. Without an
    # isolated cache file this test passes on a fresh machine and silently
    # short-circuits to a cached URL on the second consecutive run.
    with patch("telepress.core.TelegraphAuth") as auth, patch("telepress.core.time.sleep"), \
            patch("telepress.core.CACHE_FILE", str(tmp_path / "dedup-cache.json")), \
            patch.dict("os.environ", {"TELEPRESS_API_KEY": "pagination-test"}):
        auth.return_value.get_client.return_value = client
        response = TestClient(app).post("/publish/text", json={
            "content": content, "title": "Reference regression", "token": "fake",
        }, headers={"X-TelePress-Key": "pagination-test"})
    assert response.status_code == 200, response.text
    pages = [call.kwargs["content"] for call in client.create_page.call_args_list]
    assert len(pages) > 1
    link = pages[0][0]["children"][0]
    assert link["tag"] == "a"
    assert link["attrs"]["href"] == "https://example.com/reference"
    assert "".join(text_of(n) for page in pages for n in page) == "Reference" + "测试正文。" * 10_000


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
