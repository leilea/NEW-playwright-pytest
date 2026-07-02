## MODIFIED Requirements

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
