import client from './client.ts';
import { PageData } from '../types.ts';

// --- 类型定义 (参考 OpenAPI Schema) ---

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

export interface UpdatePasswordParams {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export interface UpdateEmailParams {
  new_email: string;
  code: string;
}

export interface LoginHistoryItem {
  login_id: number;
  login_time: string;
  logout_time: string | null;
  ip_address: string;
  user_agent: string | null;
  login_status: 'success' | 'failed' | 'expired' | 'forced_logout';
}

// --- API 方法 ---

// 1. 获取当前用户信息
export const getUserProfile = () => {
  return client.get<any, UserMe>('/v1/user/me');
};

// 2. 更新用户名
export const updateUsername = (username: string) => {
  return client.patch<any, UserMe>('/v1/user/me', { username });
};

// 3. 更新密码
export const updatePassword = (data: UpdatePasswordParams) => {
  return client.put<any, void>('/v1/user/me/password', data);
};

// 4. 更新头像
export const updateAvatar = (avatarUrl: string) => {
  return client.post<any, { avatar_url: string }>('/v1/user/me/avatar', { avatar_url: avatarUrl });
};

// 5. 发送邮箱验证码
export const sendEmailVerificationCode = (newEmail: string) => {
  return client.post<any, void>('/v1/user/me/email/send-code', { new_email: newEmail });
};

// 6. 确认修改邮箱
export const confirmUpdateEmail = (data: UpdateEmailParams) => {
  return client.put<any, UserMe>('/v1/user/me/email', data);
};

// 7. 获取登录历史 (分页)
export const getLoginHistory = (page: number = 1, pageSize: number = 10) => {
  return client.get<any, PageData<LoginHistoryItem[]>>('/v1/user/me/login-history', {
    params: { page, page_size: pageSize }
  });
};