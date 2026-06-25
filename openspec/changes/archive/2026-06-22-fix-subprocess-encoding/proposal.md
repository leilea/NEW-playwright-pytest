## 为什么

在 Windows 系统中 `stdout.encoding=gbk`，后端两个子进程边界（`playback.py` 和 `rec_ws.py`）使用 `.decode(errors="replace")` 未显式指定 UTF-8 编码。当 Python 子进程输出包含中文时，GBK 字节被误作为 UTF-8 解码，中文变为 `�` 乱码，导致回放错误日志和录制日志中的中文文本无法正确显示，严重阻碍调试。

## 变更内容

- 在 `playback.py` 子进程调用中强制 UTF-8 模式（`-X utf8` + `PYTHONUTF8=1`），并将 stdout/stderr 解码改为显式 `encoding="utf-8"`
- 在 `rec_ws.py` 的 stdout/stderr 解码中也显式指定 `encoding="utf-8"`

## 功能 (Capabilities)

### 新增功能

- `subprocess-utf8-stdio`: 所有子进程 stdio 边界统一使用 UTF-8 编码，确保中文输出（含错误日志、录制步骤）在任意系统编码环境下均能正确传递和显示

### 修改功能

<!-- 无 -->

## 影响

- `backend/app/services/playback.py`: `Popen` 调用添加 `-X utf8` + `PYTHONUTF8=1`，2 处 `.decode()` 改为显式 UTF-8
- `backend/app/ws/rec_ws.py`: 2 处 `.decode()` 改为显式 UTF-8
