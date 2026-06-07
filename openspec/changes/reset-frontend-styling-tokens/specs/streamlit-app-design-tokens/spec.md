## 新增需求

### 需求:设计令牌系统
系统必须通过 CSS 变量集中定义颜色 / 字号 / 间距 / 圆角 / 阴影 / 行高等设计令牌，并通过 Streamlit 全局 CSS 注入在所有页面生效。

#### 场景:令牌文件存在且可被加载
- **当** Streamlit 应用启动
- **那么** `streamlit_app/assets/design_tokens.css` 必须被读取并通过 `<style>` 标签注入到页面

#### 场景:令牌语义化命名
- **当** 维护者阅读 `design_tokens.css`
- **那么** 必须看到按用途分组的 CSS 变量（如 `--color-bg` / `--color-accent` / `--space-4` / `--text-base`），而非具体值

#### 场景:令牌可被未来前端直接复用
- **当** 文件被复制到未来的 Vue/TS 项目
- **那么** 不需要任何翻译或转换即可使用同一组变量名

### 需求:字号全局收紧
系统必须将默认字号从 Streamlit 默认（body 16~18px、h1 ~32px、metric value 32px）收紧到 QA 工作台适配的紧凑尺寸（body 14px、h1 24px、metric value 22px）。

#### 场景:页面正文与标题字号调整
- **当** 用户打开任一页面
- **那么** 正文段落必须以 14px 渲染；h1 必须以 24px 渲染

#### 场景:metric 数值与标签字号调整
- **当** 页面渲染 `st.metric`
- **那么** 数值必须以 22px 渲染；标签必须以 12px 渲染

### 需求:主题与主色
系统必须以浅色为默认主题，accent 必须使用靛蓝 `#6366F1`，状态色必须与 accent 解耦。

#### 场景:浅色主题基线
- **当** 应用启动
- **那么** 背景必须为 `#FAFAFA`、表面必须为 `#FFFFFF`、主文字必须为 `#1A1A1A`

#### 场景:accent 应用于交互元素
- **当** 用户看到主按钮 / 链接 / 焦点环
- **那么** 颜色必须为靛蓝 `#6366F1`

#### 场景:状态色与 accent 不冲突
- **当** 状态色（通过 / 失败 / 警告 / 跳过）被使用
- **那么** 颜色必须分别为 `#10B981` / `#EF4444` / `#F59E0B` / `#6B7280`，且不得与 accent `#6366F1` 重合

### 需求:零业务代码修改
本次样式重置必须仅通过 CSS 注入完成，所有 `page_*.py` 文件不得被修改。

#### 场景:页面业务逻辑不变
- **当** 实施完成后运行 `git diff streamlit_app/page_*.py`
- **那么** 输出必须为空

#### 场景:controllers / services / utils / types 不变
- **当** 实施完成后运行 `git diff streamlit_app/controllers streamlit_app/services streamlit_app/utils streamlit_app/types`
- **那么** 输出必须为空（除 `utils/style.py` 是新增外）

### 需求:迁移接缝
必须提供一个明确的"接缝"模块，未来切到 TypeScript / Vue 时该模块可被整体删除并替换为标准的 `import './styles/tokens.css'`。

#### 场景:接缝函数存在
- **当** 维护者查看 `streamlit_app/utils/style.py`
- **那么** 必须看到 `inject_design_system()` 函数，并且文件顶端注释必须说明迁移时如何替换

#### 场景:接缝函数被 app.py 调用
- **当** Streamlit 启动
- **那么** `streamlit_app/app.py` 必须在 `set_page_config` 之后调用一次 `inject_design_system()`

### 需求:深色模式接口预留
令牌文件必须预留深色模式扩展点（注释或选择器占位），但本轮不实现深色规则。

#### 场景:深色模式占位存在
- **当** 维护者查看 `design_tokens.css`
- **那么** 必须看到形如 `/* TODO dark mode: add :root[data-theme="dark"] { ... } */` 的注释或空选择器

## 修改需求

无

## 移除需求

无
