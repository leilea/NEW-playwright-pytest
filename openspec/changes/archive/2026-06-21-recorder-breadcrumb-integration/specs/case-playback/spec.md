## MODIFIED Requirements

### 需求:回放支持自愈

系统执行回放时，必须支持可选的 pytest-breadcrumb 自愈机制。

#### 场景:启用 breadcrumb 回放
- **当** breadcrumb_enabled 配置为 true
- **那么** 生成的脚本使用 `crumb()` 包装 page 对象
- **那么** 首次回放时各元素指纹存入 `.breadcrumb.db`

#### 场景:关闭 breadcrumb
- **当** breadcrumb_enabled 配置为 false 或环境变量 `BREADCRUMB_ENABLED=false`
- **那么** 生成的脚本不包含 breadcrumb 包装，使用原始 Playwright page 对象

#### 场景:breadcrumb 自愈
- **当** 页面改版导致原始选择器失效
- **那么** pytest-breadcrumb 扫描全页匹配指纹
- **那么** 匹配成功后回放继续、不中断
