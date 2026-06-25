## 上下文

Windows 系统默认编码为 GBK（cp936），而 Python 3 的 `bytes.decode()` 在未指定 encoding 参数时默认使用 UTF-8。当前代码中：

- `playback.py:28-33`: `Popen` 子进程未传递 `-X utf8` / `PYTHONUTF8=1`，子进程 stdout/stderr 使用 GBK 输出中文
- `playback.py:37-38`: `.decode(errors="replace")` 未指定 encoding → 默认为 UTF-8 → GBK 字节被误解码，中文变乱码
- `rec_ws.py:92,106`: 同样的问题，录制日志中的中文步骤信息也会损坏

`rec_ws.py` 的 `Popen` (line 75-82) 已经正确传递了 `-X utf8` + `PYTHONUTF8=1`，但 `.decode()` 仍然没有显式 encoding。

`runner.py:25,31` 已正确使用 `encoding="utf-8"`，可作为参考实现。

## 目标 / 非目标

**目标：**
- 确保所有子进程 stdio 边界的编码一致为 UTF-8
- 修复 `playback.py` 的子进程编码（缺失 `-X utf8`）
- 修复 `playback.py` 和 `rec_ws.py` 中 `.decode()` 缺少显式 encoding 的问题

**非目标：**
- 不涉及文件 I/O 编码（`.py` 文件已正确使用 `encoding="utf-8"`）
- 不修改 `runner.py`（已正确处理）

## 决策

**双层修复：**

1. **子进程侧**：`playback.py` 的 `Popen` 添加 `-X utf8` 参数 + `env["PYTHONUTF8"] = "1"`，确保子进程以 UTF-8 模式输出
2. **接收侧**：所有 `.decode()` 添加显式 `encoding="utf-8"` 参数

这是防御纵深策略。即使某一层失效，另一层仍能保证正确性。`rec_ws.py` 已有第 1 层（子进程 UTF-8），只需补第 2 层。`playback.py` 两层都需要补。

**备选方案（不采用）：**
- 仅改 `.decode()` 不设子进程 UTF-8：在 Windows 上子进程仍输出 GBK，`.decode("utf-8")` 会因字节非 UTF-8 而触发 `errors="replace"`，仍然丢失数据
- 仅设子进程 UTF-8 不改 `.decode()`：子进程输出 UTF-8，但 `.decode()` 可能在不同系统上有不同默认行为
- 全局设置 `PYTHONUTF8=1`：影响范围太大，不在本次修复范围内

## 风险 / 权衡

- [低风险] 修复后子进程输出中可能包含更多非 ASCII 字符（之前被 `errors="replace"` 吞掉了），但这是正确的行为
- [无回滚风险] 变更仅影响 stdout/stderr 的文本显示，不影响业务逻辑
