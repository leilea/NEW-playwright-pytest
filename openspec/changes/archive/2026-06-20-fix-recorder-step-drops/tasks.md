## 1. 恢复实时捕获 + 序列号去重

- [x] 1.1 JS 端：`rec()` 添加自增 `seq` 序号，恢复 `console.log` 调用
- [x] 1.2 Python 端：恢复 `handle_console()` 函数，添加 `_emitted_seqs` 集合去重
- [x] 1.3 Python 端：`flush_queue()` 添加 seq 去重
- [x] 1.4 恢复 `page.on("console", handle_console)` 注册

## 2. 修复 fillTimer 全局单例

- [x] 2.1 JS 端：将 `fillTimer` 改为 `fillTimers` Map，按元素独立去抖

## 3. 修复异常静默吞错

- [x] 3.1 `flush_queue()` 中 `except Exception: pass` 改为记录 stderr 日志

## 4. 验证

- [x] 4.1 Python 语法检查通过
