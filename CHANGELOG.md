实现了jrrp的基本功能, 尝试设定回复模板机制

新增群消息复读功能：
- 支持 `repeat_match` 正则触发复读
- 支持 `repeat_time` 连续相同消息阈值触发（默认 5）
- 同一条消息内容仅复读一次
- 复读逻辑拆分到 `group_message_handler`，仅在群消息中生效
- 增加 `_conf_schema.json` 对应配置项

群消息与贴表情（aiocqhttp）：
- 从 `message_obj` 取出 `message` 段列表；仅当每一段均为文本（`type == text` 的 Raw 段）时进入复读排队与触发，避免表情/图片等混入复读
- 「贴表情」指令：首段为 `Plain` 且正文为「贴表情」，次段为 `Face` 时取 `Face.id`，`await set_msg_emoji_like`；第二段缺失、非表情或缺少 id 时回复 `bot.reply.emoji_like_failed` 模板
- 线上一版修正：`message_id` 取自 `message_obj.message_id`；指令与表情段使用 AstrBot 的 `Plain` / `Face` 组件判断，替代裸 dict 的 `type` / `data` 取值