## 上下文

**当前状态**：
- `streamlit_app/app.py:7-12` 调用 `st.set_page_config` 但未指定 `theme` 参数；Streamlit 走默认主题（浅色、body font 16~18px、metric value 32px）
- `streamlit_app/assets/` 目录存在但为空（既无 CSS 也无图片资源）
- 5 个 `page_*.py` 全部直接用 `st.title` / `st.subheader` / `st.metric` / `st.dataframe` 等原语，零自定义样式
- 项目内已有 4 个 archived openspec 变更 + 4 个 specs 目录，架构层（controllers / services / utils / types）已为未来前端迁移分好层

**约束**：
- 不修改 `page_*.py` 的业务代码（视觉调整必须通过 CSS 覆盖完成，对调用方透明）
- 不引入新依赖（CSS 注入走 `st.markdown(unsafe_allow_html=True)`）
- 不动 `tests/`、`conftest.py`、`pytest.ini`
- 设计令牌必须**框架无关**（CSS 变量），未来 Vue/TS 可直接 `cp` 到 `tokens.css` / `tokens.ts`

**利益相关者**：当前维护者（想要更紧凑的 QA 工作台视觉）、未来前端迁移方（想要可复用的设计令牌层）

## 目标 / 非目标

**目标**：
- 全局 body 字号从 16~18px 降到 14px；h1 从 ~32px 降到 24px；metric value 从 32px 降到 22px
- 建立分层令牌系统：`.streamlit/config.toml`（框架原子）→ `design_tokens.css`（语义变量）→ `global.css`（Streamlit 类名覆盖）
- 提供一个迁移"接缝"（`streamlit_app/utils/style.py:inject_design_system()`），未来切到 Vue 时删除该文件、改为 `import './styles/tokens.css'`
- 浅色主题、靛蓝 `#6366F1` accent、与状态色（绿/红/黄）不冲突

**非目标**：
- 不实现深色模式（tokens 中留 `[data-theme="dark"]` 接口、不写规则）
- 不重写 page_*.py 的列宽、container 层次、按钮逻辑
- 不动 controllers / services / utils / types 任何文件
- 不引入第三方 CSS 框架（Tailwind、Bootstrap 等）
- 不做组件抽离 / 不引入 Storybook

## 决策

### 决策 1：用 CSS 变量做令牌，不做 SCSS / CSS-in-JS

**采用**：`design_tokens.css` 用原生 CSS custom properties（`--color-bg`、`--space-4` 等），global.css 消费这些变量写 Streamlit 类名覆盖。

**理由**：
- Streamlit 注入的 CSS 没有预处理步骤；SCSS 会引入构建依赖
- CSS 变量是 W3C 标准，浏览器原生支持，零运行时开销
- 未来 Vue/TS 用 `<style>` 块或 `tokens.css` 都能直接消费同一份变量
- Streamlit 在 `<style>` 标签里写 CSS 完全合法

**替代方案**：
- ❌ SCSS 变量：需要 sass 编译；Streamlit 不带构建步骤
- ❌ CSS-in-JS（emotion / styled-components）：Streamlit 不是 React 生态，引入徒增复杂度
- ❌ Python f-string 生成 CSS：失去 IDE 语法高亮，diff 噪声大

### 决策 2：拆 2 个 CSS 文件（tokens + global），不合并

**采用**：`design_tokens.css`（只定义变量） + `global.css`（`@import` tokens 后写规则）。

**理由**：
- tokens 与规则解耦，未来切到 Vue 时只复制 tokens 即可，规则部分由 Vue 组件 scoped style 接管
- 单文件过大不利于审阅 diff；现状约 80 + 120 行可读性更好
- `style.py` 只需读 1 个文件（global.css 已经 `@import` tokens），但 git 历史里两个文件各自演进

**替代方案**：
- ❌ 合并为 1 个文件：未来切 Vue 要手动拆分，违反 KISS
- ❌ 拆 4+ 文件（color.css / typography.css / spacing.css ...）：项目体量不需要

### 决策 3：用 `st.markdown(<style>...</style>, unsafe_allow_html=True)` 注入，不写自定义 component

**采用**：在 `app.py` 顶部 `st.set_page_config` 之后调用 `inject_design_system()`，内部把 global.css 读出来后包一层 `<style>` 用 markdown 注入。

**理由**：
- Streamlit 官方支持且最简单
- 注入只发生一次（app 启动时），运行时无开销
- 不需要新增 `components/` 目录、不需要前端 build 工具
- 未来删除 `style.py` + 取消 `app.py` 中的 1 行调用 = 100% 还原现状

**替代方案**：
- ❌ Streamlit 自定义 component（需要 React + build）：工程量过大，价值不匹配
- ❌ 让用户手动在浏览器装 Stylus 插件：违反"项目自带"原则
- ❌ 在 `st.set_page_config` 里用 `theme` 字段：Streamlit 1.x 的 theme 配置项很有限（仅 base / primaryColor / backgroundColor / textColor / font），无法覆盖 metric / button / dataframe 等子组件

### 决策 4：浅色 + 靛蓝 accent，与状态色（绿/红/黄）解耦

**采用**：
- 背景 `#FAFAFA`、表面 `#FFFFFF`、文字 `#1A1A1A`、次要文字 `#6B7280`、边框 `#E5E7EB`
- Accent `#6366F1`（靛蓝）仅用于：主按钮 / 链接 / 焦点环
- 状态色独立：成功 `#10B981` / 危险 `#EF4444` / 警告 `#F59E0B` / 跳过 `#6B7280`

**理由**：
- QA 仪表盘需要清晰区分"通过/失败/跳过/损坏"4 个语义，accent 不能与"成功绿"撞色
- 靛蓝是 frontend-design 推荐的"克制技术感"主色，与中性灰背景形成恰当对比度
- 与侧栏 Playwright 绿色 logo 不冲突（logo 仍用品牌色，不替换为靛蓝）

**替代方案**：
- ❌ Playwright 绿 `#2EAD33` 做 accent：与"通过"状态色撞色，违反 frontend-design "One accent color by default unless the product already has a multi-color system" 原则
- ❌ 多 accent 色：QA 工具不需要多色系统，增加视觉噪声

### 决策 5：tokens 中预留 `[data-theme="dark"]` 选择器但不实现

**采用**：tokens 注释里标注 `/* TODO dark mode: add :root[data-theme="dark"] { --color-bg: ... } */`，但本轮不写深色规则。

**理由**：
- 给未来需求留接口，避免下次重设计时再返工
- 实现成本低（注释即可），未来打开时不需要重排 token 顺序

**替代方案**：
- ❌ 本轮就实现深色：scope 蔓延，且需要 toggle UI + session_state 持久化，工作量翻倍

## 风险 / 权衡

- **[风险] Streamlit 版本升级可能改类名导致覆盖失效** → 缓解：用 `[data-testid="stMainBlockContainer"]` 等基于 testid 的选择器，比类名更稳定；tokens 不依赖任何类名
- **[风险] `unsafe_allow_html=True` 在 Streamlit 未来版本可能被收紧** → 缓解：Streamlit 1.x 至今一直支持，官方未表态弃用；迁移到 Vue 时这一步自然消失
- **[权衡] CSS 注入发生在每次页面重渲（每次 st.rerun）** → 接受：`inject_design_system()` 只在 `app.py` 顶层调用一次（不在页面内调用），实际重渲不会重复注入；Streamlit 的 `app.py` 只跑一次
- **[权衡] 失去 Streamlit 用户在 UI 里切深色的能力** → 接受：本轮明确不做深色；留 token 接口
- **[风险] Plotly 图表的 `width='stretch'` 与新容器 padding 可能错位** → 缓解：page_dashboard.py 已有 `width='stretch'` 占满新容器宽度；如需进一步调整可作为后续微调任务

## 迁移计划

**部署步骤**（无破坏性）：
1. 新增 `streamlit_app/assets/design_tokens.css`
2. 新增 `streamlit_app/assets/global.css`
3. 新增 `streamlit_app/utils/style.py`
4. 新增 `.streamlit/config.toml`
5. 修改 `streamlit_app/app.py`：在 `set_page_config` 之后新增 2 行（`from streamlit_app.utils.style import inject_design_system` + `inject_design_system()`）
6. 启动 streamlit，逐页目视检查 5 个页面

**未来 TS/Vue 迁移对应**：
| 现在 | 未来 |
|---|---|
| `design_tokens.css` | `web/src/styles/tokens.css`（直接复制） |
| `global.css` 的类名覆盖 | 删除；改为 Vue 组件 `<style scoped>` |
| `utils/style.py` | 删除 |
| `app.py` 中的 2 行 | 删除 |
| `.streamlit/config.toml` | 改用 Vue 的 `vite.config.ts` + `theme.css` |

**回滚策略**：
- 单次 `git revert` 即可恢复 `app.py` 2 行
- 删除 4 个新文件即完全还原
- 零数据库/状态变更，零用户数据风险

## 开放问题

无
