## 上下文

登录接口 `POST /api/auth/login` 的 `LoginIn.email` 字段使用 `EmailStr` (Pydantic)，严格校验 email 格式。默认管理账号 `admin@local` 因域名缺少句点被拒绝。用户要求改为"登录账号"方式，接受任意字符串。

## 目标 / 非目标

**目标：**

- 登录接口接受任意字符串作为账号（不再校验 email 格式）
- 前端登录表单文案改为"登录账号"
- API 请求体字段名保持 `email`，不做 breaking change

**非目标：**

- 不新增 `username` 数据库字段
- 不修改 JWT payload 中的 `email` 键名
- 不改动数据库结构

## 决策

- 保持请求体字段名为 `email`（避免前端/客户端 breaking change），仅放宽类型校验
- `UserOut.email` 同步改为 `str`，避免 `/api/auth/me` 返回时同样抛 `EmailStr` 异常
- 前端仅改 label 文案，变量名和 API 调用保持原样

## 风险 / 权衡

- 后续若需分离"账号 vs 真实邮箱"，需加 `username` 列并迁移；当前无此需求
