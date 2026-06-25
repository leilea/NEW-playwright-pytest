## 为什么

系统用例列表页面缺少创建日期列，用户无法直观看到每个系统的创建时间。后端已存储 `created_at` 字段，只需前端展示。

## 变更内容

- 在系统用例列表（Suites.vue）"描述"列右侧新增"系统创建日期"列
- 列宽与其他列保持均分
- 格式化日期为 `YYYY-MM-DD HH:mm` 显示
- 新增系统后，由于后端 `server_default=func.now()` 自动填充，创建日期会直接展示

## 功能 (Capabilities)

### 新增功能

- `suite-created-at-column`: 系统列表新增创建日期展示列

### 修改功能

<!-- 无 -->

## 影响

- `frontend/src/pages/Suites.vue`：新增一列
