## 1. 后端：放宽 email 校验

- [x] 1.1 将 `schemas/auth.py` 中 `LoginIn.email` 的类型从 `EmailStr` 改为 `str`
- [x] 1.2 将 `schemas/auth.py` 中 `UserOut.email` 的类型从 `EmailStr` 改为 `str`

## 2. 前端：更改登录表单文案

- [x] 2.1 将 `Login.vue` 中表单标签从"邮箱"改为"登录账号"

## 3. 验证

- [x] 3.1 确认 `POST /api/auth/login` 接受 `admin@local` 作为登录账号（已通过代码审查）
- [x] 3.2 确认 `GET /api/auth/me` 不再报 `EmailStr` 校验错误（已通过代码审查 + 单元测试通过）
