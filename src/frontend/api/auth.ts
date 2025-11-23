// src/api/auth.ts
import client from './client';
// 假设您现有的 UserRole 定义在 types 目录
import { UserRole } from '../types';

// --- 类型定义 (参考 API 文档 V1.3) ---

// 2.3 登录请求参数
export interface LoginRequest {
  username: string; // 文档中可能是 email，但 Login.tsx 使用 username，请根据后端实际情况调整
  password: string;
}

// 2.3 登录响应结构
export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    user_id: number;
    username: string;
    email: string;
    is_admin: boolean; // 后端返回的是 boolean
    avatar_url: string;
  };
}

// 2.2 注册请求参数
export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
  verification_code: string;
}

// 2.2 注册响应结构
export interface RegisterResponse {
  user_id: number;
  username: string;
  email: string;
  created_at: string;
}

// --- API 方法定义 ---

export const authApi = {
  /**
   * 2.1 发送注册验证码
   * @param email 用户邮箱
   */
  sendRegisterCode: (email: string) => {
    return client.post<void, void>('/auth/register/send-code', { email });
  },

  /**
   * 2.2 用户注册
   * @param data 注册表单数据
   */
  register: (data: RegisterRequest) => {
    return client.post<any, RegisterResponse>('/auth/register', data);
  },

  /**
   * 2.3 用户登录
   * @param data 登录凭证
   */
  login: (data: LoginRequest) => {
    return client.post<any, LoginResponse>('/auth/login', data);
  },

  /**
   * 2.4 用户登出
   * 注意：需要 Token，client 拦截器会自动添加
   */
  logout: () => {
    return client.post<void, void>('/auth/logout');
  },
};