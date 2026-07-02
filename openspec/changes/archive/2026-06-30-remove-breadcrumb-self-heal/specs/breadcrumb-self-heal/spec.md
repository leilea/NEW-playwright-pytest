## 移除需求

### 需求:元素自愈

**Reason**: pytest-breadcrumb（v0.1.0a2 预发布 alpha 版）在项目中产生实际价值极小——录制后即时回放场景下页面 DOM 几乎不变，自愈机制从不触发。同时引入了兼容性问题（HealableLocator.first 是方法而非属性）。完整移除该功能。

**Migration**: 生成的 Playwright 脚本不再调用 `crumb()` 包装 page 对象，直接使用原生 Playwright Page。定位策略和行为完全不变。

### 需求:配置管理

**Reason**: 随 breadcrumb 功能一并移除，不再需要 breadcrumb_enabled 配置项和 BREADCRUMB_ENABLED 环境变量。

**Migration**: 删除 config.py 中的 breadcrumb_enabled 字段。删除所有传参链路。
