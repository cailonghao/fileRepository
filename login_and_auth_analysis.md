# 登录与登录态 (Login & Auth) 模块分析报告

## 1. 核心综述
本项目采用基于 **JWT (JSON Web Token)** 的无状态身份验证体系。登录成功后，服务器会颁发一个加密 Token，客户端后续请求需在 Header 中携带该 Token 以维持登录态。

## 2. 登录流程 (Login Flow)

### 2.1 身份验证机制
- **密码加密**: 系统支持多种加密方式（BCrypt, SHA256, MD5）。
- **加盐逻辑**: 验证时会将“原始密码 + 系统安全密钥 (`SecureKey`)”进行比对，增加了安全性。
- **双端入口**:
    - **Web端**: `SysUserController.login` -> `SysUserServiceImpl.login`。
    - **App端**: `AppV1BaseController.login` -> `AppV1BaseBiz.login`。

### 2.2 Token 生成
- 使用 `cn.hutool.jwt.JWT` 库进行签名。
- **Payload 载荷**: 包含 `userId`（核心标识）和 `lang`（语言偏好）。
- **有效期**: 在 `application.yml` 中配置，Web 端和 App 端可以设置不同的过期时间。
- **格式**: 返回格式为标准 `Bearer <JWT_TOKEN>`。

## 3. 登录态维护 (Login State)

### 3.1 无状态校验
服务器端不存储 Session，而是通过 `SecurityUtil.parseJWTToken` 对请求携带的 Token 进行：
1. **签名一致性校验**: 确保 Token 未被篡改。
2. **有效期校验**: 确保 Token 未过期。
3. **合法性校验**: 确保 Token 在预设的生效时间之后。

### 3.2 自定义工具类
- **`SecurityUtil`**: 提供密码比对、Token 创建、Token 解析的底层能力。
- **`RequestUtil`**: 封装了从当前 Servlet 请求中快速提取 `userId` 等 JWT 信息的方法，供业务层使用。

### 3.3 Token 续期 (Refresh)
App 端提供了 `refreshToken` 接口。当 Token 即将过期但仍在有效期内时，客户端可以调用此接口换取新的 Token，实现无感续期。

## 4. 权限与上下文集成
登录成功后或获取权限时：
- **菜单拉取**: 系统会根据 `userId` 查询 `SysMenu`（Web）或 `AppRoleMenu`（App）。
- **权限判定**: 提供 `isPerm(userId, perm)` 方法，用于在接口调用时进行 `@AppCode` 注解授权校验。

---
**总结**: 系统通过 JWT 实现了高性能、可扩展的身份验证。配合 Hutool 工具类，代码逻辑清晰且安全性较高，能够很好地支撑 Web 和 Mobile 双端并发访问。
