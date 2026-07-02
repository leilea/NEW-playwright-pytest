## 需求

### 需求:语义定位优先级

录制系统必须按照以下优先级生成选择器，优先使用最可靠的方式。

#### 场景:定位优先级链
- **当** 录制系统为元素生成选择器
- **那么** 按以下顺序尝试：label（with for/aria-labelledby）→ label（text 匹配）→ aria-label → role+name → text（content, exact=True）→ placeholder → role-only → data-testid → CSS id → name → tag 名

#### 场景:Element Plus 表单标签检测
- **当** 录制系统为 `.el-form-item` 内的表单元素生成选择器
- **且** 传统 HTML label 关联（`for` / `aria-labelledby` / 父级 `<label>`）不可用
- **那么** 系统必须从同级 `.el-form-item__label` 提取标签文本
- **那么** 该标签文本用于 `__label:` 候选，评分 8

#### 场景:裸角色定位器唯一性
- **当** 录制系统为仅知角色、无名称的元素生成选择器
- **那么** 系统必须检查页面上具有相同角色的元素实际数量
- **那么** 仅当该角色唯一的元素时标记为 unique=true
- **那么** 当角色不唯一时，继续到上下文链 / CSS id / XPath 回退

#### 场景:父级无标识时回退元素自身 ID
- **当** 候选定位器不唯一
- **且** 语义父级和 CSS 父级上下文均未找到
- **且** 元素自身有合法 id（非纯数字开头）
- **那么** 系统必须使用 `#<elementId> > <bestCandate>` 作为链式定位器

### 需求:元素标签限定

录制系统的所有语义选择器必须携带目标元素的标签名用于消除歧义。

#### 场景:所有选择器追加标签
- **当** genSelector 生成语义选择器
- **那么** 选择的元素标签名（非 div/span/body/html）以 `|tag` 格式追加到选择器末尾
- **那么** data-testid 和 CSS 选择器不追加 |tag

#### 场景:文本定位唯一性检查
- **当** 使用文本定位前
- **那么** 使用 `document.evaluate` 计数匹配文本的元素
- **那么** 唯一匹配时直接使用文本定位；多匹配时由 `|tag` 后缀消除歧义

### 需求:选择器前缀转换

脚本生成器必须将录制产生的语义选择器前缀转换为对应的 Playwright API。

#### 场景:前缀映射
- **当** 选择器以 `__label:` 开头
- **那么** 生成 `page.get_by_label(...)`
- **当** 选择器以 `__placeholder:` 开头
- **那么** 生成 `page.get_by_placeholder(...)`
- **当** 选择器以 `__role:` 开头
- **那么** 生成 `page.get_by_role(...)`
- **当** 选择器以 `__text:` 开头
- **那么** 生成 `page.get_by_text(..., exact=True)`
- **当** 选择器以 `__testid:` 开头
- **那么** 生成 `page.get_by_test_id(...)`
- **当** 选择器无前缀
- **那么** 生成 `page.locator(...)`
