from astrbot.core.platform.astr_message_event import AstrMessageEvent
from astrbot.core.star.base import Star

from .jrrp import send_jrrp_msg

# 新增 all-message 指令时只在此处注册；群复读会据此忽略这些纯文本且不进入复读队列
_ALL_MESSAGE_HANDLERS = {
    ".jrrp": send_jrrp_msg,
}


def should_exclude_from_group_repeat(message_str: str) -> bool:
    return (message_str or "").strip() in _ALL_MESSAGE_HANDLERS


async def message_handler(bot: Star, event: AstrMessageEvent):
    message_str = (event.message_str or "").strip()
    handler = _ALL_MESSAGE_HANDLERS.get(message_str)
    if handler is None:
        return
    async for result in handler(bot, event):
        yield result
