"""Bounded text extraction for direct and quoted Feishu attachments."""
from __future__ import annotations

from collections.abc import Callable
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def extract_text_document(cached_path: str, media_type: str, *, max_bytes: int,
                          display_name: Callable[[str], str]) -> str:
    declared_text = Path(cached_path).suffix.lower() in {".txt", ".md"}
    if not cached_path or not (media_type.startswith("text/") or (
        declared_text and media_type in {"", "application/octet-stream"}
    )):
        return ""
    try:
        if os.path.getsize(cached_path) > max_bytes:
            return ""
        ext = Path(cached_path).suffix.lower()
        if ext not in {".txt", ".md"} and media_type not in {"text/plain", "text/markdown"}:
            return ""
        content = Path(cached_path).read_text(encoding="utf-8-sig")
        return f"[Content of {display_name(cached_path)}]:\n{content}"
    except (OSError, UnicodeDecodeError):
        logger.warning("[Feishu] Failed to inject text document content from %s", cached_path, exc_info=True)
        return ""


async def resolve_reply_documents(adapter: Any, message_id: str, msg_type: str, raw_content: str,
                                  mentions: Any, text: str | None) -> tuple[str | None, bool]:
    """Resolve only the quoted message; never cache a transient download failure.

    Resources use the same bot and bounded extraction as direct uploads. Returned
    content remains quoted user data; this helper never mutates prompts or permissions.
    """
    normalized = adapter._normalize(msg_type, raw_content, mentions)
    if not normalized.media_refs:
        return text, True
    paths, types = await adapter._download_feishu_message_resources(
        message_id=message_id, normalized=normalized,
    )
    parts = [text] if text else []
    for path, media_type in zip(paths, types):
        extracted = await adapter._maybe_extract_text_document(path, media_type)
        parts.append(extracted or f"[Referenced attachment saved at: {path}; content not inlined]")
    cacheable = len(paths) >= len(normalized.media_refs)
    if not cacheable:
        parts.append("[Referenced attachment download failed; original content unavailable; retry message resource retrieval]")
    return "\n\n".join(parts), cacheable
