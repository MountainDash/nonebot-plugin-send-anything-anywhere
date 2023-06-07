# 单元测试

针对单元测试的场景，峯驰物流开发了相应的测试插件。（本章节假设用户对 nonebug 有一定了解）

## 安装插件

```bash
poetry add --group dev nonebug-saa
```

## 使用说明

对于任何通过 saa 发送的消息，都可以通过 `should_send_saa` 函数来测试发送的内容。

对于这样的 matcher:

```python
@matcher_to_test.handle()
async def _():
    ...
    await MessageFactory("pong").send()
```

应该使用类似单元测试进行测试：

```python
from nonebug_saa import should_send_saa

async def test_a_matcher(app):

    ...

    async with app.test_matcher(matcher_to_test) as ctx:
        bot = ctx.create_bot(base=Bot)

        event = fake_group_message_event(message=Message("ping"), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_pass_rule()
        ctx.should_pass_permission()
        should_send_saa(
            ctx,
            MessageFactory("pong"),
            bot,
            event=event,
        )
```

需要注意的是，`should_send_saa` 传入的内容应该和 `MessageFactory.send()` 中传入的内容**一致**，如果是以这样的形式发送：

```python
await MessageFactory("pong").send(reply=True)
```

那么，测试代码应该相对应地改为：

```python
should_send_saa(
    ctx,
    MessageFactory("pong"),
    bot,
    event=event,
    reply=True
)
```

并且，如果使用 `MessageFactory.send()` 方式发送消息，需要传入 event。

对于主动发送，并且自动选择 bot 的场景，如果在上下文中仅创建了一个默认 adapter（类型为 fake）的bot，那么一定会选择这个 bot。（大部分时候不需要主动关心这个功能）
