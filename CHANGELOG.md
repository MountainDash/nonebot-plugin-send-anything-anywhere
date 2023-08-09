# Change Log

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

