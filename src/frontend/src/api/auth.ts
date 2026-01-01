/**
 * @file auth.ts
 * @module API/Authentication
 * @description 用户认证与账户安全 API 服务模块。
 * 本模块作为系统的统一身份验证入口，实现了基于 JWT (JSON Web Token) 的认证机制 [cite: 326]。
 * 核心功能涵盖：用户注册验证流、多因素登录认证、会话生命周期管理（SF10）以及
 * 基于 SMTP 邮件网关的密码找回与重置逻辑 [cite: 217, 237]。
 * @author Wang Lirong (王利蓉)
 * @version 1.3.0
 * @date 2026-01-02
 */

import client from './client.ts';

// --- 类型定义 (参考 API 文档 V1.3) ---

/**
 * 2.3 登录请求参数接口
 * @interface LoginRequest
 * @description 封装用户登录时提交的身份凭证数据。
 * @property {string} username - 用户的唯一登录识别码或注册用户名。
 * @property {string} password - 用户登录密码（前端传输前应符合基础长度策略）。
 */
export interface LoginRequest {
  username: string;
  password: string;
}

/**
 * 用户核心信息结构
 * @interface UserMe
 * @description 存储当前登录用户的完整业务画像，包括权限等级与资源配额 [cite: 221]。
 * @property {number} user_id - 用户在全球系统中的唯一主键 ID。
 * @property {string} username - 注册用户名。
 * @property {string} email - 已验证的电子邮箱地址。
 * @property {string} status - 账户活跃状态：正常、挂起或封禁 [cite: 490-493]。
 * @property {number} used_databases - 当前已创建的数据库项目总量，用于配额校验 [cite: 375]。
 * @property {number} max_databases - 系统允许该用户拥有的最大项目上限，默认通常为 10 [cite: 90, 226]。
 * @property {string | null} avatar_url - 用户头像的托管地址。
 * @property {boolean} is_admin - 角色标识：是否拥有系统管理员运维权限 [cite: 331]。
 * @property {string | null} last_login_at - 最近一次登录系统的 ISO 8601 时间戳 [cite: 506]。
 * @property {string} created_at - 账号创建（注册）的原始时间。
 */
export interface UserMe {
  user_id: number;
  username: string;
  email: string;
  status: 'normal' | 'suspended' | 'banned';
  used_databases: number;
  max_databases: number;
  avatar_url: string | null;
  is_admin: boolean;
  last_login_at: string | null;
  created_at: string;
}

/**
 * 2.3 登录响应数据结构
 * @interface LoginData
 * @description 适配后端 UnifiedResponse<LoginData> 的标准负载结构。
 * @property {string} access_token - JWT 访问令牌，有效期为 120 分钟 [cite: 327]。
 * @property {string} token_type - 令牌类型，通常为 "Bearer"。
 * @property {UserMe} user - 返回当前登录用户的详细档案对象。
 */
export interface LoginData {
  access_token: string;
  token_type: string;
  user: UserMe;
}

/**
 * 2.2 注册请求参数接口
 * @interface RegisterRequest
 * @description 封装用户通过邮箱验证码进行新账号注册所需的数据字段 [cite: 457]。
 * @property {string} username - 拟注册的用户名。
 * @property {string} email - 用于接收验证码并绑定账号的邮箱地址 [cite: 612]。
 * @property {string} password - 设置的符合安全策略的原始密码。
 * @property {string} confirm_password - 用于二次核对的确认密码字段。
 * @property {string} verification_code - 从邮件网关收到的 6 位或 8 位数字验证码。
 */
export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
  verification_code: string;
}

/**
 * 2.2 注册成功的响应结构
 * @interface RegisterResponse
 */
export interface RegisterResponse {
  user_id: number;
  username: string;
  email: string;
  created_at: string;
}

/**
 * 忘记密码发起请求的参数接口
 * @interface ForgotPasswordRequest
 */
export interface ForgotPasswordRequest {
  email: string;
}

/**
 * 结合验证码执行密码重置的请求接口
 * @interface ResetPasswordWithCodeRequest
 */
export interface ResetPasswordWithCodeRequest {
  email: string;
  verification_code: string;
  new_password: string;
  confirm_password: string;
}

// --- API 方法定义 ---

/**
 * 认证模块 API 调用核心对象
 * 封装了所有涉及系统准入与账号治理的通讯逻辑
 */
export const authApi = {
  /**
   * 2.1 向指定邮箱发送注册验证码
   * 本接口调用外部 SMTP 邮件网关。若服务商限制频率，可能影响准入效率 [cite: 237]。
   * @method sendRegisterCode
   * @param {string} email - 目标接收邮箱
   */
  sendRegisterCode: (email: string) => {
    return client.post<void, void>('/v1/auth/register/send-code', { email });
  },

  /**
   * 2.2 提交用户注册申请
   * 系统将验证验证码的有效性并检查用户名/邮箱是否冲突。
   * 注册成功后将自动分配初始数据库额度 [cite: 561]。
   * @method register
   * @param {RegisterRequest} data - 注册表单全量数据
   */
  register: (data: RegisterRequest) => {
    return client.post<any, RegisterResponse>('/v1/auth/register', data);
  },

  /**
   * 2.3 用户登录验证
   * 验证用户凭证并返回访问令牌。登录成功后，前端应将会话存入持久化存储 [cite: 236]。
   * @method login
   * @param {LoginRequest} data - 登录凭证（用户名与密码）
   * @returns {Promise<LoginData>} 包含令牌及用户画像的响应数据 [cite: 326]
   */
  login: (data: LoginRequest) => {
    return client.post<any, LoginData>('/v1/auth/login', data);
  },

  /**
   * 2.4 用户安全登出
   * 清除后端的认证状态。前端拦截器会自动在 Header 中附带 JWT Token。
   * 退出后将清除本地会话信息并跳转至登录页 [cite: 461]。
   * @method logout
   */
  logout: () => {
    // 调用登出接口执行服务端 Session 销毁逻辑
    return client.post<void, void>('/v1/auth/logout');
  },

  /**
   * 忘记密码：发起验证码重置流程
   * 系统将检查邮箱是否存在，若存在则发送重置专用验证码 [cite: 245, 612]。
   * @method sendPasswordResetCode
   * @param {string} email - 绑定的账户邮箱
   */
  sendPasswordResetCode: (email: string) => {
    // 构造重置请求载荷
    const payload: ForgotPasswordRequest = { email };
    return client.post<void, void>('/v1/auth/forgot-password', payload);
  },

  /**
   * 重置密码：结合邮箱验证码完成最终修改
   * 验证通过后直接更新底层数据库加密存储的密码 [cite: 612]。
   * @method resetPasswordWithCode
   * @param {ResetPasswordWithCodeRequest} data - 包含验证码及新密码的数据体
   */
  resetPasswordWithCode: (data: ResetPasswordWithCodeRequest) => {
    // 提交重置逻辑，更新账户安全凭据
    return client.post<void, void>('/v1/auth/reset-password', data);
  },
};