## 上下文

DSEP Test Platform 前端基于 Vue 3 + Element Plus，当前所有样式通过内联 `style` 属性硬编码，完全依赖 Element Plus 默认主题，缺乏品牌识别和视觉统一性。

约束：
- 必须保持 Element Plus 组件 API 不变，不影响现有业务逻辑
- 必须保持向后兼容，不引入新的构建依赖
- 不修改页面结构和路由

## 目标 / 非目标

**目标：**
- 通过 CSS 变量覆盖建立品牌主题，统一视觉基调
- 引入 Inter 字体提升文本可读性
- 清理内联硬编码样式，替换为语义化 CSS 变量或 scoped style
- 优化关键视觉节点（登录页、导航栏、表格、卡片）

**非目标：**
- 不引入 SCSS / Tailwind 等新构建依赖
- 不重构页面布局或组件结构
- 不修改 Element Plus 组件源码
- 不添加动画库或动效系统（可在后续变更中单独处理）

## 决策

### D1：CSS 变量覆盖 vs SCSS 体系重建
**选择**：CSS 变量覆盖
**理由**：Element Plus 原生支持 `--el-*` CSS 变量覆盖，无需额外依赖；改动量最小（约 5-8 文件），新页面零成本继承。SCSS 体系更适合后续深色模式等复杂需求时引入，当前不应过度设计。

### D2：Inter 字体 vs 系统默认字体
**选择**：引入 Inter（Google Fonts），中文 fallback 为系统字体
**理由**：Inter 是专为 UI 优化的无衬线字体，x-height 高、数字等宽、可读性极佳，在技术产品中广泛使用。通过 `<link>` 标签引入，无构建负担。

### D3：品牌主色
**选择**：#4A90D9（天蓝）
**理由**：用户明确选择清新现代风格。天蓝色传达专业而不失亲和力，适合测试管理工具定位。生成完整的 Light 色阶覆盖 Element Plus 的 primary 系列变量。

### D4：内联样式处理策略
**选择**：优先替换为 Element Plus 语义 CSS 变量（如 `var(--el-bg-color-page)` 替代硬编码 `#f5f7fa`），仅在无法匹配时使用 scoped style
**理由**：最大化复用 Element Plus 主题体系，保持响应主题变更的能力。

## 风险 / 权衡

- **Inter 字体加载影响首屏** → 使用 `font-display: swap` 确保文字立即可见，System font stack 作为 fallback
- **硬编码样式遗漏** → 按文件逐个迁移，重点处理高流量页面（Dashboard、Login、MainLayout）
- **品牌色与其他状态色冲突** → Primary 色系独立覆盖，Success/Warning/Danger 仅微调避免过于突兀
