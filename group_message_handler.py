import asyncio
import json
import re
from pathlib import Path

from astrbot.core.message.components import Face, Plain
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
from astrbot.core.star.base import Star

from .message_handler import should_exclude_from_group_repeat
from .utils import render_text_template

_EMOJI_QCID_MAP: dict[str, int] | None = None


def _get_emoji_qcid_map() -> dict[str, int]:
    """读取并缓存本地 emojiId -> qcid 映射。"""
    global _EMOJI_QCID_MAP
    if _EMOJI_QCID_MAP is not None:
        return _EMOJI_QCID_MAP

    index_path = Path(__file__).with_name("config").joinpath("qq_emoji_index.json")
    try:
        with index_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        _EMOJI_QCID_MAP = {}
        return _EMOJI_QCID_MAP

    mapping: dict[str, int] = {}
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            emoji_id = item.get("emojiId")
            qcid = item.get("qcid")
            if isinstance(emoji_id, str) and isinstance(qcid, int):
                mapping[emoji_id] = qcid

    _EMOJI_QCID_MAP = mapping
    return _EMOJI_QCID_MAP


def _raw_message_segments(message_obj: object) -> list | None:
    """从 RawMessage 风格载荷取出 ``message`` 数组；缺失或类型非 list 时为 None。"""
    if message_obj is None:
        return None
    if isinstance(message_obj, dict):
        segments = message_obj.get("message")
    else:
        segments = getattr(message_obj, "message", None)
    if not isinstance(segments, list):
        return None
    return segments


def _message_segments_are_all_text(segments: list | None) -> bool:
    """``message`` 数组非空且每一段都是 ``Plain`` 时为真。"""
    if segments is None or not segments:
        return False
    return all(isinstance(seg, Plain) for seg in segments)


async def group_message_handler(bot: Star, event: AiocqhttpMessageEvent):
    group_id = event.get_group_id()
    message = _raw_message_segments(event.message_obj)
    is_plain_text = _message_segments_are_all_text(message)
    message_str = (event.message_str or "").strip()

    if is_plain_text:  # 纯文本消息, 考虑复读
        if not message_str:
            return

        if should_exclude_from_group_repeat(message_str):
            return

        if not hasattr(bot, "group_repeat_state") or bot.group_repeat_state is None:
            bot.group_repeat_state = {}

        state = bot.group_repeat_state.setdefault(
            str(group_id),
            {"queue": [], "last_repeat_message": None},
        )

        queue = state["queue"]
        queue.append(message_str)
        if len(queue) > 30:  # 保留最近的30条消息
            queue.pop(0)

        # 如果消息匹配到配置中的正则表达式, 且和上次复读内容不同, 则复读
        repeat_match = bot.config.get("repeat_match") or ""
        if repeat_match:
            try:
                matched = re.match(repeat_match, message_str)
            except re.error:
                matched = False
            if matched and message_str != state["last_repeat_message"]:
                yield event.plain_result(message_str)
                state["last_repeat_message"] = message_str
                return

        # 如果最新的n条消息完全相同, 且和上次复读内容不同, 则复读
        repeat_time = bot.config.get("repeat_time")
        if repeat_time is not None:
            repeat_time = int(repeat_time)
            if repeat_time > 0 and len(queue) >= repeat_time:
                recent_messages = queue[-repeat_time:]
                if (
                    len(set(recent_messages)) == 1
                    and message_str != state["last_repeat_message"]
                ):
                    yield event.plain_result(message_str)
                    state["last_repeat_message"] = message_str
                    return

    # 实现对指令的处理
    if message:
        first_segment = message[0]
        if isinstance(first_segment, Plain):
            cmd_text = (first_segment.text or "").strip()

            # 贴表情
            if cmd_text.startswith("贴表情"):
                emoji_like_list = []
                for msg in message:
                    if len(emoji_like_list) > 20:
                        break
                    if isinstance(msg, Face):
                        emoji_like_list.append(msg.id)
                    elif isinstance(msg, Plain):
                        # 提取所有emoji字符
                        emoji_id = re.findall(r"[^\u4e00-\u9fa5]", msg.text)
                        if emoji_id:
                            emoji_qcid_map = _get_emoji_qcid_map()
                            for current_emoji_id in emoji_id:
                                qcid = emoji_qcid_map.get(current_emoji_id, "")
                                emoji_like_list.append(qcid)

                emoji_like_list = [item for item in emoji_like_list if item != ""]

                if len(emoji_like_list) == 0:
                    nickname = bot.config.get("nickname") or bot.name
                    style_name = bot.config.get("style")
                    fail_text = render_text_template(
                        style_name,
                        "bot.reply.emoji_like_failed",
                        {"nickname": nickname},
                        "{nickname}不知道要贴什么表情喵w~",
                    )
                    yield event.plain_result(fail_text)
                    return

                for emoji_id in emoji_like_list:
                    await event.bot.set_msg_emoji_like(
                        message_id=(event.message_obj or {}).message_id,  # pyright: ignore[reportAttributeAccessIssue]
                        emoji_id=emoji_id,
                        set=True,
                    )
                    # 等待0.3秒
                    await asyncio.sleep(0.3)
                return
