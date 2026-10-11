"""Reply attachments must reach the current user turn, not just filename placeholders."""
import asyncio
import json
from collections import OrderedDict
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from tests.gateway import test_feishu as feishu_tests
from plugins.platforms.feishu.adapter import FeishuAdapter


def parent_response():
    parent = SimpleNamespace(msg_type="file", mentions=[], body=SimpleNamespace(content=json.dumps({
        "file_key": "file_report", "file_name": "report.md",
    })))
    return SimpleNamespace(success=lambda: True, data=SimpleNamespace(items=[parent]))


def test_reply_document_original_reaches_dispatched_context_and_cache(tmp_path):
    adapter = feishu_tests.TestFeishuProcessInboundMessage()._build_adapter()
    adapter._fetch_message_text = FeishuAdapter._fetch_message_text.__get__(adapter)
    adapter._client = Mock()
    adapter._message_text_cache = OrderedDict()
    adapter._build_get_message_request = Mock(return_value=object())
    adapter._run_blocking = AsyncMock(return_value=parent_response())
    path = tmp_path / "report.md"
    original = "# Findings\nOriginal first item\n" + "Long body\n" * 800 + "FINAL_SENTINEL"
    path.write_text(original)
    calls = []
    async def download(*, message_id, normalized):
        calls.append(message_id)
        return ([str(path)], ["application/octet-stream"]) if message_id == "parent" else ([], [])
    adapter._download_feishu_message_resources = download
    message = SimpleNamespace(content=json.dumps({"text": "check this report"}), message_type="text",
        message_id="current", mentions=[], chat_id="oc_chat", parent_id="parent", thread_id=None)
    asyncio.run(adapter._process_inbound_message(data=message, message=message, sender_id=None,
        chat_type="group", message_id="current"))
    event = adapter._dispatch_inbound_event.call_args.args[0]
    assert event.text == "check this report"
    assert event.reply_to_message_id == "parent"
    assert original in event.reply_to_text
    assert asyncio.run(adapter._fetch_message_text("parent")) == event.reply_to_text
    assert calls.count("parent") == 1


def test_reply_download_failure_stays_explicit_and_retryable_with_size_limit(tmp_path):
    adapter = feishu_tests.TestFeishuFetchMessageText()._build_adapter()
    adapter._run_blocking = AsyncMock(return_value=parent_response())
    path = tmp_path / "report.md"
    path.write_text("RECOVERED_CONTENT")
    adapter._download_feishu_message_resources = AsyncMock(side_effect=[([], []), ([str(path)], ["application/octet-stream"])])
    failed = asyncio.run(adapter._fetch_message_text("parent"))
    assert "download failed" in failed.lower()
    assert "parent" not in adapter._message_text_cache
    assert "RECOVERED_CONTENT" in asyncio.run(adapter._fetch_message_text("parent"))
    path.write_text("x" * (101 * 1024))
    assert asyncio.run(adapter._maybe_extract_text_document(str(path), "application/octet-stream")) == ""
    unknown = tmp_path / "payload.bin"
    unknown.write_text("not a declared text document")
    assert asyncio.run(adapter._maybe_extract_text_document(str(unknown), "application/octet-stream")) == ""
