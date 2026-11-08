# Change Log

## 最近更新

- :arrow_up: bump dependencies and support Python 3.10-3.14 [@felinae98](https://github.com/felinae98) ([#200](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/200))
- :construction_worker: 修复 Netlify 文档构建（固定 pnpm 版本） [@felinae98](https://github.com/felinae98) ([#202](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/202))

### 文档

- rename `xxx` to `Xxx` [@montmorill](https://github.com/montmorill) ([#178](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/178))

## v0.7.1

### Bug 修复

- nonebot.adapters.discord 应在 try 块内导入 [@AzideCupric](https://github.com/AzideCupric) ([#171](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/171))

## v0.7.0

### 破坏性变更

- 不再支持 Python 3.8 [@AzideCupric](https://github.com/AzideCupric) ([#156](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/156))

### 新功能

- 适配 Discord 适配器 [@AzideCupric](https://github.com/AzideCupric) ([#162](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/162))
- 添加MentionAll [@AzideCupric](https://github.com/AzideCupric) ([#161](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/161))
- 明确PlatformTarget的deserialize类方法返回`AllSupportedPlatformTarget`类型 [@AzideCupric](https://github.com/AzideCupric) ([#160](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/160))

### Bug 修复

- 修复注释参数错误 [@itsevin](https://github.com/itsevin) ([#166](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/166))

### 文档

- 补充主页 Readme 的文档说明 [@AzideCupric](https://github.com/AzideCupric) ([#154](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/154))

## v0.6.1

### 新功能

- 适配 satori 适配器 [@he0119](https://github.com/he0119) ([#118](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/118))

## v0.6.0

### 破坏性变更

- 移除 qqguild 适配器 [@he0119](https://github.com/he0119) ([#148](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/148))

### 新功能

- 兼容 Pydantic V2 [@he0119](https://github.com/he0119) ([#147](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/147))
- 适配 telegram 适配器的 Reply Segment，向 TelegramMessageID 添加了 `chat_id` 参数 [@lgc2333](https://github.com/lgc2333) ([#145](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/145))

### Bug 修复

- 放宽AggregatedMessageFactory.__init__的类型约束 [@AzideCupric](https://github.com/AzideCupric) ([#132](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/132))

### 文档

- 移除 QQGuild 相关文档 [@he0119](https://github.com/he0119) ([#149](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/149))
- 完善使用文档 [@AzideCupric](https://github.com/AzideCupric) ([#133](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/133))

## v0.5.0

### 破坏性变更

- 将 Reply 的 data 字段统一为 dict [@AzideCupric](https://github.com/AzideCupric) ([#129](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/129))

### 新功能

- 为 Receipt 添加 MessageId 的转换支持 [@AzideCupric](https://github.com/AzideCupric) ([#130](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/130))
- 引入config，并为QQ频道添加 magic_msg_id 相关配置 [@AzideCupric](https://github.com/AzideCupric) ([#131](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/131))
- 去除MessageFactory和MessageSegmentFactory的泛型，补充成员方法 [@AzideCupric](https://github.com/AzideCupric) ([#128](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/128))
- 适配qq适配器 [@AzideCupric](https://github.com/AzideCupric) ([#105](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/105))
- 导出 OpenID Target [@Dreamail](https://github.com/Dreamail) ([#123](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/123))
- 引入 QQ群 和 QQ私聊 的 openid target [@felinae98](https://github.com/felinae98) ([#119](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/119))

## v0.4.0

### 破坏性变更

- 重构 Reply [@felinae98](https://github.com/felinae98) ([#97](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/97))

### 新功能

- 适配 DoDo [@AzideCupric](https://github.com/AzideCupric) ([#114](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/114))
- 支持选择特定 Bot 的 PlatformTarget [@felinae98](https://github.com/felinae98) ([#116](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/116))
- 为 auto select bot 加入更多日志信息 [@felinae98](https://github.com/felinae98) ([#101](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/101))

### Bug 修复

- 捕获 auto select bot 功能中的各处异常 [@AzideCupric](https://github.com/AzideCupric) ([#115](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/115))

### 文档

- 修复文档错误  [@Sam5440](https://github.com/Sam5440) ([#110](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/110))
- 修复文档错误 [@montmorill](https://github.com/montmorill) ([#104](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/104))
- 更新 adapter 适配指南 [@felinae98](https://github.com/felinae98) ([#98](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/98))
- 📝 完善自动选择Bot文档 [@AzideCupric](https://github.com/AzideCupric) ([#100](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/100))

## v0.3.2

### Bug 修复

- 移除 metadata 中的 qqguild [@AzideCupric](https://github.com/AzideCupric) ([#92](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/92))

## v0.3.1

### 新功能

- Red 适配 Receipt 与合并转发 [@he0119](https://github.com/he0119) ([#85](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/85))
- 增加 SaaTarget nb 依赖项 [@felinae98](https://github.com/felinae98) ([#83](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/83))
- 适配 Red [@he0119](https://github.com/he0119) ([#76](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/76))
- 增添 message_receipt [@felinae98](https://github.com/felinae98) ([#71](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/71))

### Bug 修复

- 修复 Red 适配器撤回私聊报错的问题 [@he0119](https://github.com/he0119) ([#89](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/89))

### 文档

- :memo: 补充 enable_auto_select_bot 的说明 [@AzideCupric](https://github.com/AzideCupric) ([#87](https://github.com/MountainDash/nonebot-plugin-send-anything-anywhere/pull/87))

## v0.3.0

### 破坏性更新

- 在 TargetOB12Unknow 中加入 platform 字段 [@he0119](https://github.com/he0119) ([#63](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/63))

### 新功能

- 适配飞书 [@MeetWq](https://github.com/MeetWq) ([#66](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/66))
- 扩充 ob11 event 支持 [@MeetWq](https://github.com/MeetWq) ([#49](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/49))
- 支持 qqguild 发送dms [@he0119](https://github.com/he0119) ([#62](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/62))
- Support OB11 NotifyEvent [@ssttkkl](https://github.com/ssttkkl) ([#58](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/58))

### Bug 修复

- :bug: fix dictionary changed size during iteration error [@he0119](https://github.com/he0119) ([#64](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/64))
- 修复 qqguild extract_target 类型错误问题 [@felinae98](https://github.com/felinae98) ([#57](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/57))

## v0.2.7

### 新功能

- 支持更多 matcher 发送方法 [@felinae98](https://github.com/felinae98) ([#55](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/55))
- 支持 MessageSegment 发送 [@felinae98](https://github.com/felinae98) ([#54](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/54))

### 文档

- 增加单元测试文档 [@felinae98](https://github.com/felinae98) ([#53](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/53))

## v0.2.6

### 新功能

- 为测试增加 fake 适配器 [@felinae98](https://github.com/felinae98) ([#52](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/52))

## v0.2.5

### 新功能

- 添加 metadata [@felinae98](https://github.com/felinae98) ([#51](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/51))
- 支持 telegram [@lgc2333](https://github.com/lgc2333) ([#47](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/47))
- “找不到合适的bot”抛出特定错误 [@felinae98](https://github.com/felinae98) ([#48](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/48))

### 文档

- 搭建文档网站 [@AzideCupric](https://github.com/AzideCupric) ([#50](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/50))

## v0.2.4

- 为kaiheila适配器添加list_targets支持 [@ssttkkl](https://github.com/ssttkkl) ([#44](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/44))
- 降低 Python 版本要求至 3.8+ [@he0119](https://github.com/he0119) ([#45](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/45))
- ✨ send_to 支持自动选择合适的 bot 进行发送 [@he0119](https://github.com/he0119) ([#39](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/39))

### 新功能

- 添加反序列化带 PlatformTarget 的 pydantic 对象的支持 [@felinae98](https://github.com/felinae98) ([#42](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/42))

## v0.2.2

### 新功能

- 开启 PlatformTarget 的 orm_mode [@AzideCupric](https://github.com/AzideCupric) ([#37](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/37))
- 将 PlatformTarget 设为 frozen [@felinae98](https://github.com/felinae98) ([#36](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/36))
- 支持反序列化字典 [@felinae98](https://github.com/felinae98) ([#35](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/35))
- 添加聚合发送 [@felinae98](https://github.com/felinae98) ([#34](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/34))

## v0.2.1

### Bug 修复

- 修复未安装onebot适配器或qqguild适配器时导入报错的问题 [@ssttkkl](https://github.com/ssttkkl) ([#33](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/33))

## v0.2.0

### 新功能

- 引入 send 方法 [@felinae98](https://github.com/felinae98) ([#26](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/26))
- 添加从 event 中提取 send target 的方法 [@felinae98](https://github.com/felinae98) ([#25](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/25))
- 引入 SendTarget [@felinae98](https://github.com/felinae98) ([#24](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/24))
- 增加 overwrite 方法 [@felinae98](https://github.com/felinae98) ([#23](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/23))
- 添加 Custom 自定义消息段 [@felinae98](https://github.com/felinae98) ([#19](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/19))

### 文档

- 为Readme中的支持情况添加更直观的表格与emoji [@AzideCupric](https://github.com/AzideCupric) ([#20](https://github.com/felinae98/nonebot-plugin-send-anything-anywhere/pull/20))

## v0.1.1

### 新功能

- 添加 qqguild adapter

## v0.1.0

### 新功能

- 增加 Text, Image, Mention, Reply 类型
- 增加 Onebot v11, Onebot v12 支持

