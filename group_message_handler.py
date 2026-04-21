import re

from astrbot.core.platform.astr_message_event import AstrMessageEvent
from astrbot.core.star.base import Star


async def group_message_handler(bot: Star, event: AstrMessageEvent):
    group_id = event.get_group_id()

    message_str = (event.message_str or "").strip()
    if not message_str:
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
