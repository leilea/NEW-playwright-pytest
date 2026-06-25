## 为什么

登录接口使用 `EmailStr` (Pydantic) 校验邮箱格式，要求域名含句点，导致默认管理员 `admin@local` 无法登录。用户希望登录字段改为"登录账号"，不再强制 email 格式。

## 变更内容

1. 后端 `LoginIn.email` 类型从 `EmailStr` → `str`，去掉 email 格式校验
2. 后端 `UserOut.email` 类型从 `EmailStr` → `str`，避免 `/me` 接口同样报错
3. 前端登录表单标签"邮箱"→"登录账号"，字段名保留 `email`（不改变 API 请求体）

## 功能 (Capabilities)

### 新增功能
- `login-with-account`: 允许任意字符串作为登录凭证，不再校验 email 格式

### 修改功能
- `login`: API 请求体字段名保持 `email`，但不再要求 email 格式；前端显示改为"登录账号"

## 影响

- `backend/app/schemas/auth.py`：两个 `EmailStr` 改为 `str`
- `frontend/src/pages/Login.vue`：标签文字改为"登录账号"
- 不涉及数据库变更、不涉及 API 请求体字段名变更（向后兼容）
