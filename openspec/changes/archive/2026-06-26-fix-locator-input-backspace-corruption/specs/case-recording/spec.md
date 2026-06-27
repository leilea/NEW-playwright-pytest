## 修改需求

### 需求:步骤参数编辑稳定性

步骤编辑器中的 locator/selector 参数输入框必须在用户编辑（包括 Backspace 删除）时保持内容稳定，禁止因逐键触发全量格式转换导致内容级联损坏或光标跳转。

#### 场景:末尾 Backspace 不损坏内容
- **当** selector 输入框显示 `locator(".icon-SystemNavigation")`
- **且** 用户将光标移到文本末尾
- **且** 用户按下 Backspace 键 2 次
- **那么** 输入框内容变为 `locator(".icon-SystemNavigation`（仅删除了末尾 2 个字符）
- **且** 输入内容不会被嵌套包装为 `locator("locator(\"...")` 等损坏形式

#### 场景:中间编辑不跳转光标
- **当** selector 输入框显示 `locator(".my-button")`
- **且** 用户将光标定位到 `my` 和 `button` 之间
- **且** 用户删除 `my-` 并输入 `new-`
- **那么** 光标保持在编辑位置（不跳到末尾）
- **且** 输入内容正确显示为 `locator(".new-button")`

#### 场景:Blur 时正确同步内部格式
- **当** 用户在 selector 输入框中将 `locator(".foo")` 编辑为 `locator(".bar")`
- **且** 用户点击其他元素使输入框失焦（blur）
- **那么** 内部存储的 `row.selector` 更新为 `.bar`
- **且** 下次重新渲染时显示值仍然为 `locator(".bar")`

#### 场景:未 Blur 时 Save 仍能正确保存
- **当** 用户在 selector 输入框中将 `locator(".foo")` 编辑为 `locator(".bar")`
- **且** 用户未使输入框失焦，直接点击页面"保存"按钮
- **那么** 保存的数据中对应步骤的 selector 字段为 `.bar`（而非编辑前旧值 `.foo`）

### 需求:步骤参数编辑模式一致性

selector 参数以外的参数字段（value、url 及通用 text/number/select）的编辑行为不得因 selector 绑定变更而受影响。

#### 场景:value 字段正常编辑
- **当** 用户编辑 fill 步骤的 value 参数字段
- **那么** 字段支持正常输入和修改，无光标跳转或值损坏

#### 场景:url 字段正常编辑
- **当** 用户编辑 goto 步骤的 url 参数字段
- **那么** 字段支持正常输入和修改，无光标跳转或值损坏
