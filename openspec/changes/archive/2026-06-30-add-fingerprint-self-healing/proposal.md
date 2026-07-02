## 为什么

当前自愈选择器（`_build_fallbacks`）是纯语法推导——仅从选择器字符串推导备选定位策略（如 `__role:button:登录` → `text=登录`）。语法推导无法覆盖运行时真实 DOM 属性（如 data-testid、aria-label、id），导致前端小幅变动时 fallback 链仍可能全部失效。

引入指纹机制：每次成功交互后，抓取目标元素在 DOM 上的稳定属性（data-testid, aria-label, placeholder, text, role, id, class），存入 JSON 指纹库。后续语法 fallback 失败时，用指纹重建 Locator 作为第二层兜底，实现运行时学习。

## 变更内容

- 扩展 `_SAFE_HELPER` 模板（注入到生成脚本中的 `_safe()` 函数），加入指纹记录与恢复逻辑
- 在 `script_gen.py` 中注入指纹文件路径常量
- 指纹文件 `backend/.fingerprints.json`：以 `(route, selector)` 为 key，upsert 模式存储，带 1000 条上限、90 天过期清理
- 不改 API、DB、模型层，仅修改 `script_gen.py` 一个文件

## 功能 (Capabilities)

### 新增功能
- `fingerprint-self-healing`: 运行时属性指纹记录与恢复，在语法 fallback 链之后提供第二层自愈兜底

### 修改功能
- `self-healing-locators`: `_safe()` 函数行为扩展——成功路径新增指纹记录，失败路径新增指纹恢复层
- `script-gen-sel-fallbacks`: 无规格变化，仅实现层增强

## 影响

- `backend/app/services/script_gen.py`：~60 行新增（`_SAFE_HELPER` 模板扩展 + `generate_script()` 注入常量）
- 新增文件 `backend/.fingerprints.json`：运行期自动生成
- 生成脚本体积增加约 60 行
- 对异步迁移零阻碍（指纹 I/O 在子进程中执行）
