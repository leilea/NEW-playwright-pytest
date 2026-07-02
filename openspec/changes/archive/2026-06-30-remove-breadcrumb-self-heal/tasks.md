## 1. 依赖清理

- [x] 1.1 从 requirements.txt 移除 pytest-breadcrumb[playwright]>=0.1.0a2
- [x] 1.2 从 backend/pyproject.toml 移除 pytest-breadcrumb[playwright]>=0.1.0a2

## 2. 配置清理

- [x] 2.1 从 backend/app/config.py 删除 breadcrumb_enabled 字段及注释

## 3. 脚本生成清理

- [x] 3.1 从 script_gen.py:generate_script() 移除 breadcrumb 和 breadcrumb_id 参数
- [x] 3.2 删除 generate_script() 中 crumb() 导入和 page 包装的条件分支

## 4. 传参链路清理

- [x] 4.1 从 playback.py 移除 breadcrumb=settings.breadcrumb_enabled 和 breadcrumb_id=name 传参
- [x] 4.2 从 cases.py 移除 breadcrumb=settings.breadcrumb_enabled 传参

## 5. 验证

- [x] 5.1 运行项目现有单元测试，确认无回归
- [x] 5.2 验证生成的脚本不包含 breadcrumb 导入
- [x] 5.3 验证录制和回放端到端流程正常
