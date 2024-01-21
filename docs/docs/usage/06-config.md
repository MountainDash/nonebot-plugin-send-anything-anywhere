# 插件配置

SAA 提供了一些插件配置供用户选择开启或关闭某些功能。

:::warning[支持版本]

SAA 的配置项在 [v0.5.0](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/releases/tag/v0.5.0) 之后可以使用。

:::

SAA 使用了 [scope 配置](https://nonebot.dev/docs/next/appendices/config#插件配置)，因此配置时需要加上 [`SAA__` 前缀](https://nonebot.dev/docs/next/appendices/config#配置项解析)。

以下是 SAA 的配置项：

| 配置项                          | 类型   | 默认值   | 说明                                                           |
| ------------------------------- | ------ | -------- | -------------------------------------------------------------- |
| `SAA__USE_QQGUILD_MAGIC_MSG_ID` | `bool` | `False`  | QQ频道是否使用魔法消息ID发送主动消息，可以绕过主动消息频率限制 |
| `SAA__QQGUILD_MAGIC_MSG_ID`     | `str`  | `"1000"` | QQ频道魔法消息ID，一般不需要调整                               |
