## 上下文

录制系统的 `_findLabel(el)` 通过三种标准方式查找表单元素标签：`aria-labelledby`、`el.labels`（原生 `<label for>` 关联）、父级 `<label>` 遍历。Element Plus 等 UI 框架使用独立的 `<label class="el-form-item__label">` 元素（无 `for` 属性、非 `<input>` 的父级），导致 `_findLabel()` 返回空字符串。此时若 `placeholder` 不唯一，回退到 `__role:textbox`（裸角色），但因 `__role:role` 被无条件标记为 unique，跳过 Phase 4 的 CSS id 回退。

## 目标 / 非目标

**目标：**
1. `_findLabel()` 能识别 `.el-form-item__label` 中的标签文本
2. `__role:role` 唯一性检查改为实际计数，不再无条件标记
3. `_findParentContext()` 在父级无唯一 CSS 特征时，利用元素自身的 id 回退

**非目标：**
- 不改变整体评分排序逻辑（pref 值保持不变）
- 不新增物理定位器类型
- 不影响已存储的现有用例定位器

## 决策

### D1: 用 `el.closest('.el-form-item')` 扩展标签检测

`_findLabel()` 在现有三种方式后添加第四步：

```javascript
var formItem = el.closest('.el-form-item');
if (formItem) {
    var elLabel = formItem.querySelector('.el-form-item__label');
    if (elLabel && elLabel.textContent.trim()) return elLabel.textContent.trim();
}
```

理由：`.closest()` 查找最近匹配祖先，基于广泛支持的 CSS 选择器标准。仅在前面三种方式都返回空时执行，不影响原生表单行为。

替代方案：更通用的 `[for]` 遍历（查祖先容器中的 `<label>` 元素）——拒用，因为需要遍历所有祖先并扫描子元素，代价高。

### D2: `__role:role` 改为实际唯一性检查

```javascript
// 旧：unique: true（无条件）
// 新：unique: _countRoleMatches(role, '') <= 1
```

`_countRoleMatches(role, '')` 检查相同角色的元素数量。当角色不唯一时，该候选被跳过，程序继续到 Phase 3（上下文链）和 Phase 4（CSS id 回退）。

理由：原无条件标记导致即便存在唯一 CSS id 也选择不唯一的角色定位器，这是一个 bug。修复后，Phase 4 的 `#el-id-4667-98` 路径将被正确选中。

### D3: 父级上下文失败时回退到元素自身 id

在 Phase 3 中，当 `_findParentContext(el)` 返回 null（父级无 data-testid、无唯一 id、无唯一类名），且元素自身有有效 id 时，返回该 id 作为 CSS 选择器：

```javascript
var cssParent = _findParentContext(el);
if (cssParent) return cssParent + ' > ' + best.sel;
// 新增：父级无上下文但元素自身有 id
if (el.id && !/^\d/.test(el.id)) return '#' + CSS.escape(el.id) + ' > ' + best.sel;
```

理由：`.el-form-item` 无唯一标识时，元素自身的 id 提供了准确的作用域，且 `parent > child` 语义比纯 id 更精确。

## 风险 / 权衡

- [风险] `.el-form-item` 类名可能被其他框架或自定义组件复用 → **缓解**: `.closest()` 查找仅在 `_findLabel()` 前三种方式都失败时执行，不影响标准 HTML label 检测
- [风险] `_countRoleMatches(role, '')` 性能：空名匹配所有同角色元素 → **缓解**: 已有 `count < 2` 上限（第 234 行），匹配到第 2 个即停止
- [风险] id 是自动生成的（`el-id-4667-98`），Element Plus 升级后可能变化 → **缓解**: 这是兜底方案，新录制时会优先使用标签定位器
