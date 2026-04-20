from astrbot.api.event import filter
from astrbot.core.platform.astr_message_event import AstrMessageEvent
from astrbot.core.star.base import Star
from astrbot.core.star.context import Context
from astrbot.core.star.register import register_star as register

from jrrp import get_jrrp
from model import init_db
from utils import get_plugin_data_path


@register("helloworld", "YourName", "一个简单的 Hello World 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        data_path = get_plugin_data_path(self.name)
        init_db(data_path)

    @filter.command("jrrp")
    async def jrrp(self, event: AstrMessageEvent):
        jrrp = await get_jrrp(self, event)
        yield event.plain_result(
            f"{self.name}认为{event.get_sender_name()}今天的人品是{jrrp}喵w~"
        )

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
