## 1. 依赖管理

- [x] 1.1 `requirements.txt` 添加 `pytest-breadcrumb[playwright]>=0.1.0a2`

## 2. 配置

- [x] 2.1 `config.py` 新增 `breadcrumb_enabled: bool = True`

## 3. 脚本生成

- [x] 3.1 `generate_script()` 新增 `breadcrumb: bool = True` 和 `breadcrumb_id: str | None = None` 参数
- [x] 3.2 启用时模板插入 `from breadcrumb import crumb` + `page = crumb(page, test_id=...)`
- [x] 3.3 breadcrumb 导入失败时优雅降级到普通执行

## 4. 回放集成

- [x] 4.1 `playback.py` 传递 `settings.breadcrumb_enabled` 和 `str(case.name)` 作 breadcrumb_id
- [x] 4.2 支持环境变量 `BREADCRUMB_ENABLED=false` 覆盖

## 5. 验证

- [x] 5.1 12/12 单元测试全部通过
- [x] 5.2 脚本语法验证 (`python -c "import ast; ast.parse(open(...).read())"`)
- [x] 5.3 breadcrumb 启用/关闭两种模式脚本输出验证通过
