## 为什么

`pytest-breadcrumb`（v0.1.0a2，预发布 alpha 版）在项目中产生实际价值极小：录制后即时回放场景下页面 DOM 几乎不变，自愈机制从不触发。同时它引入了兼容性问题——`HealableLocator.first` 是方法而非 Playwright 原生的属性，导致 `_dismiss_overlays` 中 `.first.is_visible()` 抛出 `AttributeError`。继续维护一个无测试覆盖、几乎不触发且带来兼容风险的 alpha 依赖，不如直接移除。

## 变更内容

- **BREAKING**: 移除 `pytest-breadcrumb[playwright]` 依赖
- 删除 `config.py` 中的 `breadcrumb_enabled` 配置项
- 从 `script_gen.py` 中移除 `breadcrumb`/`breadcrumb_id` 参数及 `crumb()` 包装生成逻辑
- 从 `playback.py` 中移除 breadcrumb 相关传参
- 从 `cases.py` 中移除 breadcrumb 配置传递
- 归档 `openspec/specs/breadcrumb-self-heal/` 规范

## 功能 (Capabilities)

### 新增功能
<!-- 无新增功能 -->

### 修改功能
- `breadcrumb-self-heal`: 移除 breadcrumb 自愈功能。生成的回放脚本不再调用 `crumb()` 包装 page 对象。
- `case-playback`: 回放脚本生成接口签名移除 `breadcrumb` 和 `breadcrumb_id` 参数。

## 影响

- `requirements.txt` — 移除 `pytest-breadcrumb[playwright]>=0.1.0a2`
- `backend/pyproject.toml` — 移除同一依赖
- `backend/app/config.py` — 删除 `breadcrumb_enabled: bool = True`
- `backend/app/services/script_gen.py` — 删除 breadcrumb 参数/逻辑/~10行
- `backend/app/services/playback.py` — 删除 breadcrumb 传参/~2行
- `backend/app/routers/cases.py` — 删除 breadcrumb 传参/~1行
- `openspec/specs/breadcrumb-self-heal/` — 归档
