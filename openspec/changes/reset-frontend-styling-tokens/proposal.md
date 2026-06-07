## 为什么

`streamlit_app/` 的 5 个页面（仪表盘 / 测试运行 / 测试用例 / 报告 / 系统配置）完全使用 Streamlit 默认主题渲染，存在两个用户可感知的问题：

1. **字号偏大** —— Streamlit 默认 body font 16~18px、metric value 32px、h1 ~32px，在 5 列指标 / 多 tab 信息密度高的 QA 工作台场景下显得松散、占据过多纵向空间。
2. **没有专属设计系统** —— 无 `.streamlit/config.toml`、无 CSS 文件、无色板 / 字号 / 间距令牌。`page_*.py` 中虽然架构已分好层（controllers / services / utils / types），但视觉层完全依赖框架默认，与"未来可能迁移到 TypeScript / Vue"的代码组织不匹配。

本次变更只新增 4 个文件 + 改 1 个文件，业务逻辑零修改；在保留 Streamlit 的前提下建立一个**框架无关的、1:1 可迁移到 Vue/TS 的设计令牌层**。

## 变更内容

- **新增** `.streamlit/config.toml`：Streamlit 原生主题基线（浅色 + 靛蓝主色 + 紧凑字体）
- **新增** `streamlit_app/assets/design_tokens.css`：设计系统唯一可信源 —— CSS 变量集中定义色板 / 字号 / 间距 / 圆角 / 阴影 / 行高；顶端注释注明未来 Vue/TS 翻译路径
- **新增** `streamlit_app/assets/global.css`：消费令牌，覆盖 Streamlit 默认类名（`.stApp`、`.stMetric`、`.stMarkdown`、`.stButton`、`.stDataFrame`、`.stTabs`、`.stSidebar`、`.stExpander`、`.stCodeBlock`、`.stAlert`）的字体 / padding / 颜色
- **新增** `streamlit_app/utils/style.py`：注入助手 `inject_design_system()`，读两个 CSS 文件并通过 `st.markdown` 注入；这是未来 Vue 迁移的"接缝"（删掉这个文件，改成 `import './styles/tokens.css'`）
- **修改** `streamlit_app/app.py`：在 `st.set_page_config` 之后调用一次 `inject_design_system()`（仅 2 行变更）

## 功能 (Capabilities)

### 新增功能
- `streamlit-app-design-tokens`: 全局设计令牌系统 —— 颜色 / 字号 / 间距 / 圆角 / 阴影 / 行高通过 CSS 变量集中定义；以 Streamlit 全局 CSS 注入方式应用；令牌语义化命名、可被未来前端直接复用

### 修改功能
- 无（page_*.py 的业务逻辑、controllers / services / utils / types 全部不变；视觉调整通过 CSS 覆盖完成，对调用方透明）

## 影响

- **代码**：新增 4 个文件 + 改 1 个文件（约 250 行新增、2 行修改）
- **运行时**：零依赖新增；所有改动走 Streamlit 标准的 `st.markdown(unsafe_allow_html=True)` CSS 注入
- **测试代码**：无影响（项目无 UI 自动化测试）
- **用户可见行为**：字号整体缩小约 25%、行高 / padding 收紧、主按钮 / 焦点环使用靛蓝 `#6366F1` accent；数据 / 交互 / 状态机全部不变
- **可回滚**：`app.py` 撤掉 2 行调用 + 删除 4 个新文件即可恢复；零破坏性变更
