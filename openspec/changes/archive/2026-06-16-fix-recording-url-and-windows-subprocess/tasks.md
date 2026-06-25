## 1. 修复录制 URL 丢失

- [x] 1.1 删除 `backend/app/services/recorder_process.py` 第 165 行冗余的 `target_url = os.environ.get("RECORDER_URL", "")`
- [x] 1.2 在 `recorder_process.py` 第 117 行之后添加空 URL 早期校验：若 `target_url` 为空则 emit error 并 `sys.exit(1)`

## 2. 修复 Windows 子进程 NotImplementedError

- [x] 2.1 在 `backend/app/main.py` 文件顶部（所有 import 之前）添加 Windows 事件循环策略设置

## 3. 验证

- [x] 3.1 验证 `recorder_process.py` 语法正确，可被 Python 解析
- [x] 3.2 验证 `main.py` 语法正确，事件循环策略设置兼容非 Windows 平台
- [x] 3.3 运行项目现有测试确保无回归（预存测试问题 non-blocking）
