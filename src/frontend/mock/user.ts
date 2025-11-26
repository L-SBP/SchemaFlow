import { MockMethod } from 'vite-plugin-mock';

// 模拟标准响应结构
const successResponse = (data: any = null, message: string = '操作成功') => {
  return {
    code: 200,
    message,
    data,
  };
};

const errorResponse = (message: string = '操作失败', code: number = 400) => {
  return {
    code,
    message,
    data: null,
  };
};

export default [
  // 1. 修改密码接口
  {
    url: '/api/user/password',
    method: 'post',
    timeout: 100, // 模拟 1秒 延迟
    response: ({ body }: { body: any }) => {
      const { oldPassword, newPassword } = body;

      // 模拟简单的验证逻辑
      if (oldPassword === '123456') { // 假设当前密码固定是 123456
        return successResponse(null, '密码修改成功');
      } else {
        return errorResponse('当前密码不正确');
      }
    },
  },

  // 2. 发送邮箱验证码接口
  {
    url: '/api/user/email/code',
    method: 'post',
    timeout: 800,
    response: ({ body }: { body: any }) => {
      const { email } = body;
      if (!email || !email.includes('@')) {
        return errorResponse('请输入有效的邮箱地址');
      }
      return successResponse({ token: 'mock-token' }, '验证码已发送');
    },
  },

  // 3. 绑定邮箱接口
  {
    url: '/api/user/email/bind',
    method: 'post',
    timeout: 1200,
    response: ({ body }: { body: any }) => {
      const { code } = body;

      // 模拟验证码校验，假设 "123456" 是正确验证码
      if (code === '123456') {
        return successResponse(null, '邮箱绑定成功');
      } else {
        return errorResponse('验证码错误或已过期');
      }
    },
  },
] as MockMethod[];