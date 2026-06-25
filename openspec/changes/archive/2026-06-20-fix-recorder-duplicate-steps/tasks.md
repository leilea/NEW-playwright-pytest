## 1. 修复双重发射

- [x] 1.1 删除 `RECORDER_INJECT_JS` 中 `rec()` 函数内的 `console.log` 调用行
- [x] 1.2 删除 `handle_console()` 函数定义（第 162-171 行）
- [x] 1.3 删除 `page.on("console", handle_console)` 注册（第 190 行）
- [x] 1.4 验证代码语法无错误（Python 语法检查）
