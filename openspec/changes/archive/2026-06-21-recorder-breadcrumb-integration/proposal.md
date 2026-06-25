## 为什么

页面改版后录制的选择器失效，回放失败。即使有最优语义定位策略，页面 DOM 结构变化仍会导致定位失败。需要选择器自愈能力：首次执行时指纹化元素，后续失败时全页扫描按指纹匹配。

## 变更内容

- **新增** 可选的 pytest-breadcrumb 自愈框架集成：脚本生成时可选插入 `crumb()` 包装，首次运行指纹化元素，失败时自动自愈
- **新增** `breadcrumb_enabled` 配置项控制开关
- **新增** `playback.py` 传递脚本名称作为稳定 breadcrumb_id

## 功能 (Capabilities)

### 新增功能
- `breadcrumb-self-heal`: 基于 pytest-breadcrumb 的元素自愈机制

### 修改功能
- `case-playback`: 回放执行支持 breadcrumb 自愈模式；新增 breadcrumb_enabled 配置

## 影响

- **后端**：`script_gen.py` 新增 `breadcrumb`/`breadcrumb_id` 参数和包装模板；`playback.py` 传递 `breadcrumb_enabled` + case name；`config.py` 新增 `breadcrumb_enabled: bool = True`；`requirements.txt` 添加 `pytest-breadcrumb[playwright]>=0.1.0a2`
- **运行时**：首次执行自动创建 `.breadcrumb.db`；breadcrumb 失败时 fallback 到普通执行
- **配置**：可通过环境变量 `BREADCRUMB_ENABLED=false` 或配置项关闭
