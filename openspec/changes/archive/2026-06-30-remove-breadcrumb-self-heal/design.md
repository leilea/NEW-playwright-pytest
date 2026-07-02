## 上下文

`pytest-breadcrumb` 集成在项目中的入口仅一处：`script_gen.py:generate_script()` 生成的 pytest 脚本中注入 `from breadcrumb import crumb` 和 `page = crumb(page, test_id=...)` 两行代码。其余引用为配置开关（`config.py`）和参数透传（`playback.py`、`cases.py`）。不使用 `HealablePage`/`HealableLocator` 类。

## 目标 / 非目标

**目标：**
- 从代码库中完全移除 breadcrumb 依赖和所有相关逻辑
- 保证录制、元素定位和回放功能不受影响
- 清理所有相关规范文件

**非目标：**
- 不引入替代的自愈方案
- 不改变生成的 Playwright 脚本结构和定位策略

## 决策

### 决策 1：完全移除而非仅关闭开关

**选择**: 删除所有 breadcrumb 代码、依赖和配置，而非仅设 `False`。

**理由**: 仅关闭会导致死代码累积（`script_gen.py` 的条件分支、`config.py` 无用配置项、`playback.py` 无用传参），增加维护负担。完全移除一次性清理干净，且回退成本极低（重装依赖 + git revert 一行）.

**替代方案**: 设置 `breadcrumb_enabled=False` 并保留代码。风险：死代码产生混淆，未来开发者误读。

### 决策 2：不改变生成的脚本结构

**选择**: 生成的 Playwright 脚本保持原有结构（`def test_...` → `page = browser.new_page()` → 定位操作），仅去除 `crumb()` 包装行。

**理由**: `crumb()` 是透明代理，去除后生成的脚本语法完全等价。定位器行为与原生 Playwright 一致（`page.locator(...)`、`page.get_by_*()` 等不受影响）。

## 风险 / 权衡

- [风险] 未来若需要自愈 → 缓解: 可从 git history 恢复，或重新评估更成熟的方案
- [风险] 现有 breadcrumb.db 文件残留 → 缓解: 与功能无关，仅仅是运行过的副作用文件，可手动删除或加入 `.gitignore`
