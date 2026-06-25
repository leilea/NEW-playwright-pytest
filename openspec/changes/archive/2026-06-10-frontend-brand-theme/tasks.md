## 1. 基础设施

- [x] 1.1 创建 `frontend/src/styles/theme.css`：定义品牌主色 #4A90D9 的完整色阶，覆盖 `--el-color-primary-light-1` 到 `--el-color-primary-light-9`，设置圆角 `--el-border-radius-base: 6px`、表格行高、卡片阴影等变量
- [x] 1.2 在 `frontend/index.html` 中引入 Inter 字体（Google Fonts `<link>`），设置 `font-display: swap`
- [x] 1.3 在 `frontend/src/main.ts` 中 import `theme.css`（在 element-plus CSS 之后）
- [x] 1.4 更新 `frontend/src/App.vue`：全局 body 字体改为 `Inter, system-ui, ...` 并设置背景色等基础样式

## 2. 布局优化

- [x] 2.1 更新 `MainLayout.vue`：侧边栏顶部品牌区域使用品牌主色背景 + 白色文字，菜单选中高亮色匹配品牌色，清理内联 style
- [x] 2.2 更新 `Login.vue`：背景从 `#f5f7fa` 替换为品牌浅色渐变，清理内联 style 为 CSS 变量

## 3. 页面内联样式清理

- [x] 3.1 更新 `Dashboard.vue`：标题、间距等内联 style 迁移至 scoped style
- [x] 3.2 更新 `Cases.vue`：无内联 style 需要清理（已确认干净）
- [x] 3.3 更新 `Suites.vue`：内联 style 清理
- [x] 3.4 更新 `Runs.vue`：卡片 header、表格等内联 style 清理，硬编码颜色（#1e1e1e 等）替换为 CSS 变量
- [x] 3.5 更新 `Playback.vue`：终端背景色 `#1e1e1e` 替换为语义变量或 scoped style
- [x] 3.6 更新 `RecorderPanel.vue`：终端背景色替换，内联 style 清理

## 4. 验证

- [x] 4.1 运行 `npm run build` 确认无编译错误
- [x] 4.2 运行 `npm run lint` 确认类型检查通过
