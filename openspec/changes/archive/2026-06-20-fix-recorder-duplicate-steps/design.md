## 上下文

`recorder_process.py` 是一个独立子进程，通过 Playwright 启动 Chrome 浏览器、注入 JS 脚本捕获用户交互，并通过 stdout JSON lines 将步骤事件发送给父进程 `rec_ws.py`。

当前架构中，每个用户操作触发两条事件发射路径：

```
rec(action, params)
  ├── console.log('__DSEP__' + JSON)  →  handle_console(msg)  →  emit() [路径 A]
  └── queue.push({action, params})    →  flush_queue()        →  emit() [路径 B]
```

两条路径最终都调用 `emit()` 写入 stdout，导致 `rec_ws.py` 读到两份相同的 step 事件并转发给前端。

## 目标 / 非目标

**目标：**
- 每条用户操作仅 emit 一次到 stdout
- 保持实时性（延迟无明显变化）

**非目标：**
- 改动前端代码
- 改动 WebSocket 协议
- 添加去重逻辑（治标不治本）

## 决策

**决策：仅保留 `flush_queue()` 路径，移除 `handle_console()` 路径。**

理由：
- `flush_queue()` 在主循环中每 100ms 执行一次，足以保证步骤在 100ms 内被捕获，对用户无感知延迟
- 队列设计更健壮：通过 `page.evaluate()` 原子地清空 `window.__dsep_queue`，避免了 console 消息可能因页面导航或异常丢失的问题
- 单一路径消除了所有重复的可能性

替代方案及被否决原因：
- **仅用 handle_console 移除 flush_queue**：console 消息在页面导航/重载时可能丢失，不如队列可靠
- **添加去重（如 seq 号）**：增加复杂度，且不能解决根本问题（每个 emit 仍是冗余的）

具体变更：
1. `RECORDER_INJECT_JS` 中 `rec()` 函数：删除 `console.log('__DSEP__' ...)` 行
2. Python 端：删除 `handle_console()` 函数定义（第 162-171 行）
3. Python 端：删除 `page.on("console", handle_console)` 注册（第 190 行）

## 风险 / 权衡

- **延迟增加**：步骤响应从近乎实时变为最多 100ms 延迟。对录制场景无实际影响。
- **fill 去抖**：`captureFill` 已有 300ms 去抖（`input` 事件），再加上 100ms 轮询间隔，最坏情况下填值步骤延迟 ~400ms。这仍远低于人工可感知阈值。
