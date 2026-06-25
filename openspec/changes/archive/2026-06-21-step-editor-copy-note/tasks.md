## 1. Step 接口扩展

- [x] 1.1 `step.ts` 的 `Step` 接口添加 `note?: string` 可选字段

## 2. StepEditor 布局调整

- [x] 2.1 操作列拆为 Move(↑↓ width:70) 和 Ops(📋🗑 width:70)
- [x] 2.2 Parameters 和 Move 之间插入 Notes 列(width:120)
- [x] 2.3 Notes 列使用 vxe-input 双向绑定 `row.note`
- [x] 2.4 列序：# → Action → Parameters → Notes → Move → Ops

## 3. 复制功能

- [x] 3.1 Ops 列添加复制按钮(📋)
- [x] 3.2 实现 `copyStep(row)`：深拷贝、插入下方、重新编号

## 4. 验证

- [x] 4.1 TypeScript 类型检查无错误
- [x] 4.2 复制功能手动测试通过
- [x] 4.3 备注列输入/编辑/清空测试通过
