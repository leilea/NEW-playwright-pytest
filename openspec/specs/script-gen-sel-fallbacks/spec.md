## 新增需求

### 需求:语义选择器降级推导

脚本生成器必须能从语义化选择器（`__role:`, `__text:`, `__label:`, `__placeholder:`, `__testid:`）自动推导备选定位策略。

#### 场景:role 选择器推导 text 备选

- **当** 主选择器为 `__role:button:登录`
- **那么** 生成 `get_by_role("button", name="登录")` 作为主策略
- **那么** 生成 `get_by_text("登录")` 作为备选策略

#### 场景:text 选择器推导 role 备选

- **当** 主选择器为 `__text:提交`
- **那么** 生成 `get_by_text("提交")` 作为主策略
- **那么** 生成 `get_by_role("button", name="提交")` 作为备选策略

#### 场景:label 选择器推导 placeholder 备选

- **当** 主选择器为 `__label:用户名`
- **那么** 生成 `get_by_label("用户名")` 作为主策略
- **那么** 生成 `get_by_placeholder("请输入用户名")` 作为备选策略
- **那么** 生成 `page.locator("input[name=用户名]")` 作为 CSS 备选

#### 场景:placeholder 选择器推导 input CSS 备选

- **当** 主选择器为 `__placeholder:搜索`
- **那么** 生成 `get_by_placeholder("搜索")` 作为主策略
- **那么** 生成 `page.locator("input[placeholder*=搜索]")` 作为 CSS 备选

#### 场景:testid 选择器无推导

- **当** 主选择器为 `__testid:login-btn`
- **那么** 仅生成 `get_by_test_id("login-btn")` 一个策略，data-testid 被视为最可靠，无需降级

### 需求:CSS 选择器推导语义备选

脚本生成器必须能从纯 CSS 选择器中提取信息并推导语义化备选策略。

#### 场景:CSS 含 :has-text 时推导 text 和 role

- **当** 主选择器为 `.el-button--primary:has-text("确定")`
- **那么** 生成原 CSS 作为主策略
- **那么** 生成 `get_by_text("确定")` 作为备选
- **那么** 生成 `get_by_role("button", name="确定")` 作为备选

#### 场景:CSS 含 id 时不推导

- **当** 主选择器为 `#loginBtn` 或 `#btn-submit`
- **那么** 仅生成原 CSS 一个策略，id 选择器被视为足够可靠

#### 场景:普通 CSS class 提取关键词推导

- **当** 主选择器为 `.submit-order-btn`
- **那么** 从 class 名提取关键词 "submit order" 或 "提交订单"
- **那么** 生成 `get_by_text("submit order")` 和 `get_by_role("button", name="submit order")` 作为备选
- **那么** class 名中的中文字符直接作为 text 备选值

### 需求:降级推导边界

降级推导必须遵循保守原则，避免生成无效或误导性备选。

#### 场景:XPath/alt/title 不推导

- **当** 主选择器类型为 `__xpath:`、`__alt:` 或 `__title:`
- **那么** 仅生成原选择器一个策略，不推导备选

#### 场景:纯数字或过短关键词不推导

- **当** 从 class 名提取的文本关键词纯数字或长度小于 2
- **那么** 不生成 text/role 备选策略，降低误匹配风险

#### 场景:带标签限定不破坏

- **当** 选择器包含 `|tag` 后缀（如 `__text:登录|a`）
- **那么** 推导备选策略时主策略保留标签限定语法，备选策略不携带标签限定
