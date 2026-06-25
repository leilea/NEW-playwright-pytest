## 为什么

录制过程中，页面跳转（登录、点击链接导航等）后后续操作步骤丢失，导致生成的测试脚本不完整。根因有三：(1) 上次修复误删了 `console.log` 实时捕获路径，步骤仅靠队列轮询，页面跳转时队列被清空；(2) `fillTimer` 全局单例导致多字段填写时前面字段的步骤被覆盖丢失；(3) `flush_queue` 中 `except Exception: pass` 静默吞错，掩盖了可能的运行时失败。

## 变更内容

- 恢复 `rec()` 中的 `console.log` 调用和 `handle_console()` 实时捕获路径
- 保留 `flush_queue()` 队列路径作为兜底
- 在 JS 端为每条步骤添加自增序列号 `seq`，Python 端通过 `seq` 集合去重，防止双路径重复发射
- 修复 `fillTimer` 全局单例问题：改用 `Map<element, timer>` 按元素独立去抖
- 移除 `except Exception: pass`，改为记录错误日志
- 添加 `beforeunload` 事件处理器，在页面卸载前清空队列

## 功能 (Capabilities)

### 新增功能
无

### 修改功能
- `case-recording`: 修复录制过程中页面跳转导致步骤丢失、多字段填写丢失、以及错误静默丢弃的问题

## 影响

- `backend/app/services/recorder_process.py` — JS 注入脚本和 Python 端事件处理
- 无 API 变更，无 Breaking 变更
