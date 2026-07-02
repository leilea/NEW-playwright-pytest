## 上下文

当前自愈选择器实现（`add-self-healing-locators`）在代码生成时通过 `_build_fallbacks()` 从选择器字符串推导 2-5 条备选定位策略，注入 `_safe()` 运行时 helper。该方案是纯语法的——其能力上限受限于选择器字符串本身的信息量。

本设计在语法 fallback 链之后增加**指纹恢复层**：运行时从真实 DOM 元素抓取稳定属性，存入 JSON 文件，后续语法 fallback 失败时用指纹重建 Locator。

### 约束
- 仅修改 `script_gen.py`（代码生成层），不改 API、DB、模型
- 注入到生成脚本中的代码只能用 Python stdlib（`json`, `hashlib`, `pathlib`, `atexit`）
- 对异步迁移零影响（指纹 I/O 在 pytest 子进程中）

## 目标 / 非目标

**目标：**
- 在语法 fallback 全部失败后，用历史指纹重建 Locator 作为第二层兜底
- 每次成功交互自动更新指纹，保持与当前 DOM 同步
- 指纹文件体积可控（upsert 去重 + 上限 + 过期）
- 仅注入有自愈能力（`has_healing=True`）的脚本

**非目标：**
- 不引入外部依赖（不换 SQLite、不装新包）
- 不做启发式 DOM 扫描（方案三）
- 不修改 Step 数据模型（不引入 element_id 字段）
- 不改变 `_safe_locator_code()` 调用签名

## 决策

### 1. 指纹 key = `md5(route + selector[:80])[:16]`

**理由**：选择器字符串是当前架构中唯一稳定的元素标识。路由前缀提供页面级隔离。md5 截断 16 位碰撞概率极低（10^13 条以下可忽略），且比完整 selector 更紧凑。

**替代方案**：
- 用完整 selector 字符串作 key → key 过长且含特殊字符
- 引入显式 `element_id` 字段 → 需改 Step 模型，改动面太大
- 仅用 selector 作 key → 不同页面可能有同名元素

### 2. 指纹 I/O 仅在所有语法 fallback 失败后触发

**理由**：正常路径（语法策略命中）只做内存操作 + atexit 落盘，无运行时 I/O 开销。指纹恢复是冷路径，JSON 读取仅在此触发。

**替代方案**：
- 每次 `_safe()` 调用都读 JSON → 不必要的 I/O
- 完全不做指纹 → 无法从历史学习

### 3. 属性提取用 `page.locator()` 而非 `locator.evaluate()`

**理由**：`HealableLocator` 的研究表明，项目曾使用 breadcrumb 包装 Page 对象，但该包已被移除。当前生成脚本使用原生 Playwright Locator，所有 `get_attribute()` / `inner_text()` 方法均可直接用。

### 4. 指纹文件位置：`backend/.fingerprints.json`

**理由**：所有用例共享同一份指纹库，跨用例知识复用。项目级存储，`.gitignore` 可选（团队共享时可提交）。

**替代方案**：
- 按 case 分文件 → 信息孤岛，同一页面的元素无法跨 case 学习
- 按路由分文件 → 增加文件管理复杂度，收益不大（当前体量 300KB 以下）

### 5. 内存缓存 + atexit 写盘

**理由**：`_safe()` 首次调用加载 JSON 到模块级 `_FP_CACHE` dict，后续操作直接操作内存，脚本退出时通过 `atexit.register()` 一次性写回。每个生成脚本仅读写文件各一次。

## 风险 / 权衡

| 风险 | 缓解 |
|------|------|
| 并发写 JSON（多进程） → 数据丢失 | atexit 写前未加锁，但 upsert 模式幂等，最后写者获胜可接受 |
| 选择器变更 → key 漂移，旧指纹无效 | 选择器语义层稳定（录制时已归一化）；极端情况由过期清理兜底 |
| 冷启动（新元素首次运行无指纹） | 语法 fallback 链覆盖首次运行；指纹在第二次及之后生效 |
| JSON 损坏 → 脚本崩溃 | `try/except` 包裹所有 JSON 操作，损坏时降级为空指纹库 |
| 指纹误存（录错元素） → 后续恢复错误 | 路由前缀隔离 + key 去重 + last_seen 过期自动淘汰 |
