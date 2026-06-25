## ADDED Requirements

### 需求:语义定位优先级

录制系统必须按照以下优先级生成选择器，优先使用最可靠的方式。

#### 场景:定位优先级链
- **当** 录制系统为元素生成选择器
- **那么** 按以下顺序尝试：label（with for/aria-labelledby）→ label（text 匹配）→ aria-label → role+name → text（content, exact=True）→ placeholder → role-only → data-testid → CSS id → name → tag 名

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
