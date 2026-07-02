## 1. 指纹数据层

- [x] 1.1 实现 `_FP_HELPER_IMPORTS` 模板（stdlib 导入：json, pathlib, hashlib, atexit, time, os, sys）
- [x] 1.2 实现 `_FP_LOAD_SAVE` 模板（`_load_fingerprints`, `_save_fingerprints`, `_fp_key(route, selector)`）
- [x] 1.3 实现 `_FP_ATTRS` 模板（`_extract_attrs(locator)` 抓取 data-testid/aria-label/placeholder/text/role/id/class）
- [x] 1.4 实现 `_FP_BUILD` 模板（`_build_from_attrs(page, attrs)` 按优先级从属性重建 Locator）
- [x] 1.5 实现 `_FP_CLEANUP` 模板（加载时过期清理 + 保存前 LRU 淘汰）

## 2. _safe() 函数扩展

- [x] 2.1 成功路径末尾新增指纹记录调用 `_record_fingerprint(page, route, strategies[0], locator)`
- [x] 2.2 语法策略全部失败后新增指纹恢复分支 `_try_fingerprint_heal(page, route, strategies[0])`
- [x] 2.3 指纹恢复成功时回写新指纹 `_record_fingerprint(...)`
- [x] 2.4 内存缓存 `_FP_CACHE` + `atexit.register(_flush_fingerprints)` 一次性写盘

## 3. script_gen.py 集成

- [x] 3.1 拼接完整 `_FINGERPRINT_HELPER` 字符串（组合 1.1-1.5 + 2.1-2.4）
- [x] 3.2 修改 `generate_script()`：当 `has_healing=True` 时注入 `_FINGERPRINT_HELPER` 和 `FINGERPRINT_FILE` 常量
- [x] 3.3 注入指纹文件路径常量 `FINGERPRINT_FILE = Path(__file__).resolve().parent / ".fingerprints.json"`

## 4. 验证

- [x] 4.1 运行项目现有单元测试确保无回归（20 个通过，3 个预存在 DB/auth 失败，与本次无关）
- [x] 4.2 验证自愈脚本注入指纹代码（has_healing=True → 包含；has_healing=False → 不包含）
- [x] 4.3 验证纯导航脚本不注入指纹代码
- [x] 4.4 验证 JSON 损坏时降级逻辑（_fp_load 内 try/except 包裹）
