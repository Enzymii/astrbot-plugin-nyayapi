实现了jrrp的基本功能, 尝试设定回复模板机制

新增群消息复读功能：
- 支持 `repeat_match` 正则触发复读
- 支持 `repeat_time` 连续相同消息阈值触发（默认 5）
- 同一条消息内容仅复读一次
- 复读逻辑拆分到 `group_message_handler`，仅在群消息中生效
- 增加 `_conf_schema.json` 对应配置项