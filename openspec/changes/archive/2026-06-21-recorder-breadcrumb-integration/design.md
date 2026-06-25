## 上下文

回放时语义选择器也会因页面改版失效。pytest-breadcrumb 是一个轻量级自愈框架：首次运行时指纹化元素的 bounding box、tag、text、attributes，失败时全页扫描匹配指纹自动重试。

## 目标 / 非目标

**目标：**
- 脚本生成可选 breadcrumb 包装：`page = crumb(page, test_id=...)`
- playback.py 传递 `breadcrumb_enabled` 配置和原始 case name 作稳定 test_id
- config.py 新增 `breadcrumb_enabled` 开关

**非目标：**
- 不修改 pytest-breadcrumb 自身行为
- 不强制开启，默认启用但可关闭
- 不修改测试报告格式

## 决策

### 决策 1：breadcrumb_id 使用 case 原始名称

**采用**：传递 `case.name` 原始字符串（cast 到 str 防非字符串 DB 类型）作 breadcrumb_id。

**理由**：case name 在项目中唯一且稳定，DB 行级标识匹配回放上下文。

### 决策 2：面包屑生成在模板层而非每行包装

**采用**：`generate_script()` 增加 `breadcrumb=True` 时在模板开头插入 `from breadcrumb import crumb` + `page = crumb(page, test_id=...)`，后续步骤代码无需改动。

**理由**：crumb() 透明代理 page 所有定位方法，不影响生成的主逻辑代码。

## 风险 / 权衡

- **[风险]** pytest-breadcrumb 版本 0.1.0a2 非稳定版 → 缓解：降级 graceful，breadcrumb 导入失败时 fallback 到普通执行
- **[风险]** .breadcrumb.db 文件污染工作目录 → 缓解：可通过 gitignore 忽略
