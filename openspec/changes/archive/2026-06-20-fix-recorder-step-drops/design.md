## 上下文

上次修复 (fix-recorder-duplicate-steps) 删除了 `console.log` + `handle_console` 实时捕获路径，仅保留 `flush_queue()` 队列轮询。这引入了新问题：页面跳转时 `window.__dsep_queue` 随旧页面销毁，队列中未清空的步骤永久丢失。

此外存在两个预存 bug：`fillTimer` 全局单例丢失多字段填写、`except Exception: pass` 静默吞错。

## 目标 / 非目标

**目标：**
- 页面跳转前后步骤不丢失
- 每条步骤仅发射一次（无重复）
- 多字段逐个填写时每个字段的 fill 步骤都被捕获
- 异常可观测（不再静默吞错）

**非目标：**
- 改动 WebSocket 协议
- 改动前端代码

## 决策

### 决策 1：序列号去重替代单路径

恢复双路径 (`console.log` 实时 + `flush_queue` 兜底)，通过 JS 端自增 `seq` 序号 + Python 端 `set` 去重。

```
rec(action, params):
    seq = ++__dsep_seq           ← 自增序号
    queue.push({seq, action, params})
    console.log('__DSEP__' + JSON)

handle_console(msg):            ← 实时路径
    if seq not in _emitted:
        _emitted.add(seq)
        emit()

flush_queue():                  ← 兜底路径（0.1s 轮询）
    for step in queue:
        if seq not in _emitted:
            _emitted.add(seq)
            emit()
```

理由：既保留实时性（handle_console 在页面跳转前捕获），又有兜底（flush_queue 补充任何遗漏），同时 seq 去重确保不重复。

替代方案：
- 仅用 flush_queue + beforeunload：beforeunload 中 `navigator.sendBeacon` 不可靠，且同步 XHR 可能被浏览器阻止
- 仅用 handle_console：console 消息在极端情况（CSP 限制、页面崩溃）可能丢失

### 决策 2：按元素去抖 fill 事件

将 `let fillTimer` 改为 `Map<Element, timer>`，每个输入元素独立去抖：

```javascript
const fillTimers = new Map();
function captureFill(el) {
    clearTimeout(fillTimers.get(el));
    fillTimers.set(el, setTimeout(() => {
        rec('fill', {...});
        fillTimers.delete(el);
    }, 300));
}
```

理由：用户切换输入字段时，前一个字段的定时器不会被误杀。

### 决策 3：记录异常替代静默吞错

`flush_queue` 中 `except Exception: pass` 改为 `except Exception as e: sys.stderr.write(...)`。

理由：便于排查运行时问题，不影响主流程。

## 风险 / 权衡

- **seq 集合内存增长**：录制会话通常数分钟，最多数千步骤，内存可忽略 → 无需清理策略
- **console.log CSP 限制**：极少数页面禁用 console API → 队列兜底可弥补
- **fill 去抖 300ms 仍可能丢失**：用户在输入最后一位后 300ms 内触发页面跳转 → 由 JS beforeunload 事件配合同步 flush（Playwright 中 page.evaluate 在页面卸载前仍可执行，不保证 100% 但 cover 大部分场景）
