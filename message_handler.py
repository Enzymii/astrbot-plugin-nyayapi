from astrbot.core.platform.astr_message_event import AstrMessageEvent
from astrbot.core.star.base import Star

from .jrrp import send_jrrp_msg


async def message_handler(bot: Star, event: AstrMessageEvent):
    message_str = (event.message_str or "").strip()
    if message_str == ".jrrp":
        async for result in send_jrrp_msg(bot, event):
            yield result
