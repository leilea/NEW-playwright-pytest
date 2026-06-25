## MODIFIED Requirements

### 需求:选择器生成

录制系统必须生成优先使用语义定位的选择器，放弃脆弱 CSS class 定位，并为所有选择器添加元素标签限定。

#### 场景:语义定位优先
- **当** 用户点击一个有 label 关联的元素
- **那么** 录制系统优先使用 get_by_label 定位
- **当** 录制系统无法找到语义定位方式
- **那么** 降级使用 data-testid、CSS id、name 属性或标签名兜底

#### 场景:标签限定消歧
- **当** 语义选择器匹配多个元素
- **那么** 选择器自动追加 `|tag` 后缀（如 `__text:登录|a`）
- **那么** 生成的脚本使用 `page.locator("a").filter(has=page.get_by_text("登录"))` 消除歧义

### 需求:wait_for_load_state 步骤

录制系统必须支持生成 `wait_for_load_state` 步骤。

#### 场景:页面加载等待
- **当** 录制生成 goto 步骤
- **那么** 脚本自动在 goto 后追加 `page.wait_for_load_state("networkidle")`
- **当** 用户手动添加 wait_for_load_state 步骤
- **那么** 提供 domcontentloaded / load / networkidle 三种状态选择

### 需求:expect 步骤状态校验

录制系统必须支持 expect 步骤检查元素的多种状态。

#### 场景:校验元素可见
- **当** expect 步骤的 state 参数为 visible
- **那么** 生成 `expect(page.locator(...)).to_be_visible()`

#### 场景:校验元素隐藏
- **当** expect 步骤的 state 参数为 hidden
- **那么** 生成 `expect(page.locator(...)).to_be_hidden()`

#### 场景:校验元素启用/禁用
- **当** expect 步骤的 state 参数为 enabled
- **那么** 生成 `expect(page.locator(...)).to_be_enabled()`
- **当** state 参数为 disabled
- **那么** 生成 `expect(page.locator(...)).to_be_disabled()`

#### 场景:校验元素可编辑
- **当** expect 步骤的 state 参数为 editable
- **那么** 生成 `expect(page.locator(...)).to_be_editable()`
