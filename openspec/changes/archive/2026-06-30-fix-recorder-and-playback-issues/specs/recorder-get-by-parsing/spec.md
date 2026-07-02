## 新增需求

### 需求: 录制端解析 get_by_placeholder 格式

录制端必须能够解析 Playwright Codegen 输出的 `page.get_by_placeholder("...")` 链式调用格式。

#### 场景: 用户通过 placeholder 定位 textarea 并输入内容

- **当** Playwright Codegen 输出行 `page.get_by_placeholder("请输入").fill("备注内容")`
- **那么** 系统解析为 `{action: "fill", params: {selector: "__placeholder:请输入", value: "备注内容"}}`

#### 场景: 用户通过 placeholder 定位 textarea 并点击

- **当** Playwright Codegen 输出行 `page.get_by_placeholder("请输入").click()`
- **那么** 系统解析为 `{action: "click", params: {selector: "__placeholder:请输入"}}`

### 需求: 录制端解析 get_by_role 格式

录制端必须能够解析 Playwright Codegen 输出的 `page.get_by_role("...", name="...")` 链式调用格式。

#### 场景: 用户点击 role+name 定位的按钮

- **当** Playwright Codegen 输出行 `page.get_by_role("button", name="确定", exact=True).click()`
- **那么** 系统解析为 `{action: "click", params: {selector: "__role:button:确定"}}`

#### 场景: 用户在 role+name 定位的 textbox 中输入内容

- **当** Playwright Codegen 输出行 `page.get_by_role("textbox", name="备注").fill("内容")`
- **那么** 系统解析为 `{action: "fill", params: {selector: "__role:textbox:备注", value: "内容"}}`

### 需求: 录制端解析 get_by_label 格式

录制端必须能够解析 `page.get_by_label("...")` 链式调用格式。

#### 场景: 用户通过关联 label 定位输入框并输入

- **当** Playwright Codegen 输出行 `page.get_by_label("用户名").fill("admin")`
- **那么** 系统解析为 `{action: "fill", params: {selector: "__label:用户名", value: "admin"}}`

### 需求: 录制端解析 get_by_text 格式

录制端必须能够解析 `page.get_by_text("...")` 链式调用格式。

#### 场景: 用户点击文本定位的元素

- **当** Playwright Codegen 输出行 `page.get_by_text("提交", exact=True).click()`
- **那么** 系统解析为 `{action: "click", params: {selector: "__text:提交"}}`

### 需求: 录制端解析 get_by_test_id 格式

录制端必须能够解析 `page.get_by_test_id("...")` 链式调用格式。

#### 场景: 用户通过 test-id 定位元素并点击

- **当** Playwright Codegen 输出行 `page.get_by_test_id("submit-btn").click()`
- **那么** 系统解析为 `{action: "click", params: {selector: "__testid:submit-btn"}}`

### 需求: 录制端解析 get_by_alt_text 和 get_by_title 格式

录制端必须能够解析 `get_by_alt_text` 和 `get_by_title` 链式调用格式。

#### 场景: 用户点击 alt 文本定位的图片

- **当** Playwright Codegen 输出行 `page.get_by_alt_text("logo").click()`
- **那么** 系统解析为 `{action: "click", params: {selector: "__alt:logo"}}`

### 需求: 归一化不改变已有解析能力

归一化后的代码必须继续正确解析原有的 `page.locator("x")` 和 `page.fill("x", "v")` 格式（向后兼容）。

#### 场景: 原有 locator 格式仍能解析

- **当** Playwright Codegen 输出行 `page.locator(".el-textarea__inner").fill("备注")`
- **那么** 系统仍能正确解析为 `{action: "fill", params: {selector: ".el-textarea__inner", value: "备注"}}`
