## 新增需求

### 需求:定位器显示优先使用无冲突的引号
定位器显示字符串 `_q()` 在包裹值时，必须优先选择与值内容不冲突的引号类型，以最小化转义字符。

#### 场景:值含双引号不含单引号时用单引号包裹
- **当** 值是 `[data-field-id="purch_demand_name"]`
- **那么** `_q()` 返回 `'[data-field-id="purch_demand_name"]'`

#### 场景:值含单引号不含双引号时用双引号包裹
- **当** 值是 `[data-field-id='purch_demand_name']`
- **那么** `_q()` 返回 `"[data-field-id='purch_demand_name']"`

#### 场景:值同时含单引号和双引号时回退 JSON 转义
- **当** 值是 `it's "hello"`
- **那么** `_q()` 返回 `"it's \"hello\""`
