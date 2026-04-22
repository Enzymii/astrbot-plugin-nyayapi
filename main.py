from astrbot.api.event import filter
from astrbot.core.config import AstrBotConfig
from astrbot.core.platform.astr_message_event import AstrMessageEvent
from astrbot.core.star.base import Star
from astrbot.core.star.context import Context
from astrbot.core.star.register import register_star as register

from .group_message_handler import group_message_handler
from .jrrp import send_jrrp_msg
from .message_handler import message_handler
from .model import init_db
from .utils import get_plugin_data_path


@register("helloworld", "YourName", "一个简单的 Hello World 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        data_path = get_plugin_data_path(self.name)
        init_db(data_path)

    @filter.command("jrrp")
    async def jrrp(self, event: AstrMessageEvent):
        async for result in send_jrrp_msg(self, event):
            yield result

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def allMessageHandler(self, event: AstrMessageEvent):
        async for result in message_handler(self, event):
            yield result

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def groupMessageHandler(self, event: AstrMessageEvent):
        async for result in group_message_handler(self, event):  # pyright: ignore[reportArgumentType]
            yield result

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
