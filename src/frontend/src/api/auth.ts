// src/api/auth.ts
import client from './client.ts';
// 假设您现有的 UserRole 定义在 types 目录
import { UserRole } from '../types.ts';

// --- 类型定义 (参考 API 文档 V1.3) ---


export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}


// 2.3 登录请求参数
export interface LoginRequest {
  username: string;
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
    is_admin: boolean;
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
    return client.post<void, void>('/v1/auth/register/send-code', { email });
  },

  /**
   * 2.2 用户注册
   * @param data 注册表单数据
   */
  register: (data: RegisterRequest) => {
    return client.post<any, RegisterResponse>('/v1/auth/register', data);
  },

  /**
   * 2.3 用户登录
   * @param data 登录凭证
   */
  login: (data: LoginRequest) => {
    return client.post<any, ApiResponse<LoginResponse>>('/v1/auth/login', data);
  },

  /**
   * 2.4 用户登出
   * 注意：需要 Token，client 拦截器会自动添加
   */
  logout: () => {
    return client.post<void, void>('/v1/auth/logout');
  },
};