## 1. StepEditor watch 逻辑修复

- [x] 1.1 修改 `editCache` watch：将 `editCache.clear()` + 全量重建改为增量维护（新增步骤添加缓存、删除步骤移除缓存、已有步骤保留不变）

## 2. CaseEditor save 数据刷新

- [x] 2.1 修改 `save()` 函数：使用 `casesApi.update()` 返回值刷新 `form.value.steps`

## 3. 验证

- [x] 3.1 `vue-tsc --noEmit` 零错误
