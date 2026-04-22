import re

from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
from astrbot.core.star.base import Star, logger

from .message_handler import should_exclude_from_group_repeat
from .utils import render_text_template


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
    """``message`` 数组非空且每一段 ``type`` 均为 ``text`` 时为真。"""
    if segments is None or not segments:
        return False
    return all(isinstance(seg, dict) and seg.get("type") == "text" for seg in segments)


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
        if isinstance(first_segment, dict) and first_segment.get("type") == "text":
            cmd_text = (first_segment.get("data", {}).get("text") or "").strip()

            # 贴表情
            if cmd_text == "贴表情":
                second_seg = message[1] if len(message) >= 2 else None
                face_id: object | None = None
                if isinstance(second_seg, dict) and second_seg.get("type") == "face":
                    raw_id = second_seg.get("data", {}).get("id")
                    if raw_id not in (None, ""):
                        face_id = raw_id

                if face_id in (None, ""):
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

                await event.bot.set_msg_emoji_like(
                    message_id=event.message_id,
                    emoji_id=face_id,
                    set=True,
                )
                logger.info(f"贴表情: {face_id} 成功")
                return
