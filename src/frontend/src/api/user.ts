import client from './client.ts';

export interface UpdatePasswordParams {
  oldPassword: string;
  newPassword: string;
}

export interface BindEmailParams {
  email: string;
  code: string;
}

// 修改密码
export const updatePassword = (data: UpdatePasswordParams) => {
  return client.post('/user/password', data);
};

// 发送邮箱验证码
export const sendEmailVerificationCode = (email: string) => {
  return client.post('/user/email/code', { email });
};

// 绑定新邮箱
export const bindEmail = (data: BindEmailParams) => {
  return client.post('/user/email/bind', data);
};

// 获取用户信息 (可选，如果页面需要自行刷新数据)
export const getUserProfile = () => {
  return client.get('/user/profile');
};