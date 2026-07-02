## 移除需求

### 需求:回放支持自愈

**Reason**: pytest-breadcrumb 依赖已从项目中完全移除。生成的脚本不再包含 breadcrumb 包装逻辑。

**Migration**: 生成的回放脚本不再包含 `from breadcrumb import crumb` 和 `page = crumb(page, test_id=...)` 语句。`generate_script()` 接口移除 `breadcrumb` 和 `breadcrumb_id` 参数。
