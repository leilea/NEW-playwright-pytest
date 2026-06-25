## 1. playback.py 编码修复

- [x] 1.1 `Popen` 添加 `-X utf8` 参数，env 添加 `PYTHONUTF8=1`
- [x] 1.2 两处 `.decode(errors="replace")` 改为 `.decode("utf-8", errors="replace")`

## 2. rec_ws.py 编码修复

- [x] 2.1 两处 `.decode(errors="replace")` 改为 `.decode("utf-8", errors="replace")`
