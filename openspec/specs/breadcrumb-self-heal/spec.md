## 需求

### 需求:元素自愈

回放系统必须支持自动元素自愈能力：首次执行时记录元素物理特征，后续失败时通过特征匹配自动修复。

#### 场景:指纹记录
- **当** 启用 breadcrumb 的脚本首次执行
- **那么** 每个定位操作记录元素的 tag、text、bounding box、attributes 到 `.breadcrumb.db`

#### 场景:失效重试
- **当** 元素定位失败（strict mode violation 或 timeout）
- **那么** pytest-breadcrumb 扫描页面所有元素，匹配记录的指纹
- **那么** 匹配到唯一元素后自动使用该元素重试

#### 场景:breadcrumb_id 稳定性
- **当** breadcrumb 集成时
- **那么** breadcrumb_id 必须使用测试用例的原始名称
- **那么** breadcrumb_id 在不同回放之间保持稳定

#### 场景:优雅降级
- **当** pytest-breadcrumb 包未安装
- **那么** 回放降级为普通 Playwright 执行模式，不抛出导入错误

#### 场景:临时禁用
- **当** 开发人员设置环境变量 `BREADCRUMB_ENABLED=false`
- **那么** 回放跳过 breadcrumb 包装，行为与未集成时一致

### 需求:配置管理

系统必须提供 breadcrumb 开关配置。

#### 场景:默认开启
- **当** 系统启动时
- **那么** breadcrumb_enabled 配置默认值为 true

#### 场景:环境变量覆盖
- **当** 环境变量 `BREADCRUMB_ENABLED` 被设置
- **那么** 以环境变量值为准，覆盖配置文件的值
