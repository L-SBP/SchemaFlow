// mock/auth.ts
import { MockMethod } from 'vite-plugin-mock';

export default [
  // 1. 发送注册验证码
  // 对应 authApi.sendRegisterCode -> POST /auth/register/send-code
  {
    url: '/api/v1/auth/register/send-code',
    method: 'post',
    response: ({ body }) => {
      console.log('Mock: 收到发送验证码请求', body);
      return {
        code: 200,
        message: '验证码发送成功',
        data: null,
      };
    },
  },

  // 2. 用户注册
  // 对应 authApi.register -> POST /auth/register
  {
    url: '/api/v1/auth/register',
    method: 'post',
    response: ({ body }) => {
      console.log('Mock: 收到注册请求', body);
      const { username, email } = body;

      // 模拟注册成功返回的数据结构 (参考 RegisterResponse)
      return {
        user_id: Math.floor(Math.random() * 1000), // 随机生成 ID
        username: username,
        email: email,
        created_at: new Date().toISOString(),
      };
    },
  },

  // 3. 用户登录
  // 对应 authApi.login -> POST /auth/login
  {
    url: '/api/v1/auth/login',
    method: 'post',
    response: ({ body }) => {
      console.log('Mock: 收到登录请求', body);
      const { username, password } = body;

      if (username === 'user' && password === '123456') {
        // 登录成功，返回 LoginResponse 结构
        return {
          access_token: 'mock-access-token-' + Date.now(),
          token_type: 'bearer',
          user: {
            user_id: 1,
            username: 'user',
            email: 'admin@example.com',
            is_admin: false,
            avatar_url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Felix',
          },
        };
      }
      // 模拟简单的登录验证逻辑
      if (username === 'admin' && password === '123456') {
        // 登录成功，返回 LoginResponse 结构
        return {
          access_token: 'mock-access-token-' + Date.now(),
          token_type: 'bearer',
          user: {
            user_id: 1,
            username: 'admin',
            email: 'admin@example.com',
            is_admin: true,
            avatar_url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Felix',
          },
        };
      } else {
        // 登录失败模拟（通过修改状态码让 axios 拦截器捕获）
        return {
          code: 401,
          message: '用户名或密码错误 (Mock)',
          data: null,
          _status: 401, // vite-plugin-mock 特有字段，用于设置 HTTP 状态码
        };
      }
    },
  },

  // 4. 用户登出
  // 对应 authApi.logout -> POST /auth/logout
  {
    url: '/api/v1/auth/logout',
    method: 'post',
    response: () => {
      console.log('Mock: 用户已登出');
      return {
        code: 200,
        message: '登出成功',
      };
    },
  },
] as MockMethod[];