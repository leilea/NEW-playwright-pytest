## 1. 设计令牌

- [x] 1.1 创建 `streamlit_app/assets/design_tokens.css`：定义色板（`--color-bg` `#FAFAFA` / `--color-surface` `#FFFFFF` / `--color-text` `#1A1A1A` / `--color-text-muted` `#6B7280` / `--color-border` `#E5E7EB` / `--color-accent` `#6366F1` / `--color-accent-hover` `#4F46E5` / `--color-success` `#10B981` / `--color-danger` `#EF4444` / `--color-warning` `#F59E0B` / `--color-skipped` `#6B7280`）、间距（`--space-1` 至 `--space-8`，4px 步进）、字号（`--text-xs` 12 / `--text-sm` 13 / `--text-base` 14 / `--text-md` 15 / `--text-lg` 16 / `--text-xl` 18 / `--text-2xl` 20 / `--text-3xl` 24，单位 px）、字体（`--font-sans` / `--font-mono` 系统字体栈）、圆角（`--radius-sm` 4 / `--radius-md` 6 / `--radius-lg` 8）、阴影（`--shadow-sm` / `--shadow-md`）、行高（`--line-height-tight` 1.3 / `--line-height-base` 1.5 / `--line-height-relaxed` 1.6）；顶端注释注明未来 Vue/TS 翻译路径，并预留 `/* TODO dark mode: add :root[data-theme="dark"] { ... } */` 占位

## 2. Streamlit 类名覆盖

- [ ] 2.1 创建 `streamlit_app/assets/global.css`：首行 `@import './design_tokens.css'`；覆盖 `.stApp`（背景 / 字体）、`[data-testid="stMainBlockContainer"]`（padding 收到 1.25rem 1.5rem）、`.stMarkdown p` 与 `.stText`（font-size var(--text-base) / line-height var(--line-height-base)）、`.stMetric label`（font-size var(--text-xs)）、`.stMetric [data-testid="stMetricValue"]`（font-size var(--text-3xl) 22px 而非 32px）、`.stButton > button`（border-radius var(--radius-md) / font-size var(--text-sm) / accent 色）、`.stDataFrame`（表头小字号 / 紧凑行高）、`.stTabs [data-baseweb="tab"]`（accent 底线）、`.stSidebar`（表面色 surface-2 / padding 收紧）、`.stExpander`（border 颜色 / radius）、`.stCodeBlock`（font-size var(--text-xs) / 背景 surface-2）、`.stAlert`（4 个状态色分别绑到 success / danger / warning / info）

## 3. 迁移接缝

- [ ] 3.1 创建 `streamlit_app/utils/style.py`：定义 `ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"`；定义 `inject_design_system()` 函数读取 `global.css` 后用 `st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)` 注入；文件顶端 docstring 注明"未来迁移到 TypeScript / Vue 时，删除本文件，改为 `import './styles/tokens.css'`"

## 4. Streamlit 原生主题

- [ ] 4.1 创建 `.streamlit/config.toml`：写入 `[theme]` 节，`base = "light"`、`primaryColor = "#6366F1"`、`backgroundColor = "#FAFAFA"`、`secondaryBackgroundColor = "#F4F4F5"`、`textColor = "#1A1A1A"`、`font = "sans serif"`

## 5. 接入应用

- [ ] 5.1 修改 `streamlit_app/app.py`：在 `st.set_page_config(...)` 之后新增 `from streamlit_app.utils.style import inject_design_system` + `inject_design_system()` 两行；其余业务代码不动

## 6. 验证

- [ ] 6.1 启动 `streamlit run streamlit_app/app.py`，逐页目视检查「仪表盘 / 测试运行 / 测试用例 / 报告 / 系统配置」5 个页面：正文 / metric / 按钮 / 表格 / tab / sidebar 视觉均更紧凑，主按钮带靛蓝 accent
- [ ] 6.2 运行 `git diff streamlit_app/page_*.py` 确认输出为空（业务逻辑零修改）
- [ ] 6.3 运行 `git status` 确认新增 4 个文件 + 修改 1 个文件（`app.py`），无意外文件
