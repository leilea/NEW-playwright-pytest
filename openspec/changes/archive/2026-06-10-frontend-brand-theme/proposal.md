## 为什么

当前前端页面完全依赖 Element Plus 默认样式，所有样式通过内联 `style` 属性硬编码，缺乏品牌视觉统一性。作为面向用户的测试管理平台，需要建立一套干净的品牌主题体系，提升专业感和可读性。

## 变更内容

- 创建全局品牌主题 CSS 文件，覆盖 Element Plus CSS 变量（主色、圆角、阴影、间距等）
- 引入 Inter 字体作为正文字体，提升文本可读性和现代感
- 替换各页面中的内联硬编码样式为 Element Plus 语义变量或 scoped CSS
- 优化登录页背景、导航栏品牌区、表格行高等关键视觉节点
- 保持所有组件 API 和页面结构不变

## 功能 (Capabilities)

### 新增功能
- `brand-theme`: 全局品牌主题系统，通过 CSS 变量覆盖 Element Plus 默认值，注入品牌色（天蓝 #4A90D9）、字体（Inter）、统一圆角和间距

### 修改功能
<!-- 无现有规范需要修改 -->

## 影响

- 受影响文件：`App.vue`、`index.html`、`MainLayout.vue`、`Login.vue`、`Dashboard.vue` 等约 10-15 个 Vue 文件
- 新增文件：`src/styles/theme.css`（全局主题变量）
- 无需修改：后端、API、测试、配置文件
