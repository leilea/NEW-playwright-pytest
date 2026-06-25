## 新增需求

### 需求:子进程 stdio 编码统一为 UTF-8
系统在所有子进程边界必须确保 stdout/stderr 数据以 UTF-8 编码传递和解码，禁止因系统默认编码差异导致中文文本损坏。

#### 场景:Playback 子进程输出中文错误日志
- **当** pytest 回放子进程通过 stdout/stderr 输出含中文的日志（如 Playwright selector 中的 placeholder 文本）
- **那么** 接收端正确解码为可读中文文本
- **那么** 日志中不出现 `�`（U+FFFD）替换字符

#### 场景:录制子进程输出中文步骤信息
- **当** 录制子进程通过 stdout 输出含中文 placeholder/aria-label 的步骤 JSON
- **那么** WebSocket 接收端正确保持中文原文
- **那么** 转发到前端的步骤数据中中文不损坏

#### 场景:非中文系统的兼容性
- **当** 系统运行在 `LANG=en_US.UTF-8` 或 Linux 默认 UTF-8 环境中
- **那么** 显式 UTF-8 参数不影响正常行为（原本就是 UTF-8）
- **那么** 子进程仍正常工作
