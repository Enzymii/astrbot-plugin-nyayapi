import datetime
import random

from astrbot.core.platform.astr_message_event import AstrMessageEvent
from astrbot.core.star.base import Star

from .model import Jrrp
from .utils import render_text_template


async def get_jrrp(bot: Star, event: AstrMessageEvent) -> int:
    platform_name = event.get_platform_name() or ""
    source_id = event.get_platform_id() or ""
    user_id = event.get_sender_id() or ""
    group_id = event.get_group_id() or ""
    today = datetime.date.today()

    jrrp = random.randint(1, 100)

    record, _ = Jrrp.get_or_create(
        platform=platform_name,
        source_id=source_id,
        user_id=user_id,
        date=today,
        defaults={"group_id": group_id, "value": jrrp},
    )
    return record.value


async def send_jrrp_msg(bot: Star, event: AstrMessageEvent):
    jrrp = await get_jrrp(bot, event)
    nickname = bot.config.get("nickname") or bot.name
    style_name = bot.config.get("style")
    sender_name = event.get_sender_name()
    message = render_text_template(
        style_name,
        "bot.reply.jrrp",
        {
            "nickname": nickname,
            "sender_name": sender_name,
            "jrrp": jrrp,
        },
        "{nickname}认为{sender_name}今天的人品是{jrrp}喵w~",
    )
    yield event.plain_result(message)
