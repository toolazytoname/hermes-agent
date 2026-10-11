"""Air's Feishu streaming report delivery uses explicit attachments, not local links."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from gateway.config import Platform
from gateway.platforms.base import BasePlatformAdapter, SendResult
from gateway.platforms.event import MessageEvent, MessageType
from gateway.session import SessionSource
from gateway.run import GatewayRunner
from tests.gateway import test_media_resend_dedup as media_tests

@pytest.mark.asyncio
async def test_feishu_streamed_report_requires_explicit_document_attachment(tmp_path, monkeypatch):
    report = media_tests._allowed_file(tmp_path, monkeypatch, 'review.md')
    adapter = SimpleNamespace(
        name='feishu', extract_media=BasePlatformAdapter.extract_media,
        extract_images=BasePlatformAdapter.extract_images,
        send_document=AsyncMock(return_value=SendResult(success=True, message_id='doc')),
    )
    runner = SimpleNamespace(_thread_metadata_for_source=lambda *args: {}, _reply_anchor_for_event=lambda _: None)
    event = MessageEvent(text='give me the report', message_type=MessageType.TEXT,
        source=SessionSource(platform=Platform.FEISHU, chat_id='authorized-chat', chat_type='group'))
    await GatewayRunner._deliver_media_from_response(runner, f'[Report]({report})', event, adapter)
    adapter.send_document.assert_not_awaited()  # do not silently upload arbitrary paths from prose
    await GatewayRunner._deliver_media_from_response(runner, f'Report summary\nMEDIA:{report}', event, adapter)
    adapter.send_document.assert_awaited_once_with(chat_id='authorized-chat', file_path=str(report), metadata={})
