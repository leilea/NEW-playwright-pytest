# Branch Management

## 命名规范

```
fix/<short-description>     # Bug 修复
feat/<short-description>    # 新功能
refactor/<description>      # 重构
chore/<description>         # 构建/配置/工具
```

## 当前分支

| Branch | Created | Based on | Status | Description |
|--------|---------|----------|--------|-------------|
| `master` | — | — | active | 主分支，v0.1.0 |
| `fix/script-gen-step-format` | 2026-06-19 | `master@81afa8c` | merged → v0.1.0 | 步骤格式兼容 + 页签/回放/乱码修复 |

## 分支生命周期

1. **创建**: `git checkout -b fix/<name> master`
2. **开发**: 在分支上提交
3. **合并**: 合并到 master 后打 tag
4. **清理**: `git branch -d fix/<name>`
